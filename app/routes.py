from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app import db
from app.models import Appointment, Gender, Role, User, Doctor
from werkzeug.exceptions import BadRequest

main = Blueprint('main', __name__)

# registreation auth
@main.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate incoming data
    required_fields = ['email', 'password', 'firstName', 'lastName', 'gender', 'age', 'contactNum', 'profilePic', 'role']    # FIXME: Add remaining fields here for signup
    for field in required_fields:
        if field not in data:
            raise BadRequest(f'Missing required field: {field}')

    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already registered"}), 400
    
    # Check if role is valid
    if data['role'] not in [role.value for role in Role]:
        return jsonify({"message": "Invalid role"}), 400

    if data['gender'] not in [gender.value for gender in Gender]:
        return jsonify({"message": "Invalid gender"}), 400

    # Create user instance
    user = User(
        email=data['email'],
        firstName=data['firstName'],
        lastName=data['lastName'],
        age=data['age'],
        gender=data['gender'],
        contactNum=data['contactNum'],
        profilePic=data['profilePic'],
        role=data['role']
    )
    user.set_password(data['password'])  # Hash the password

    try:
        # Add user to the database and flush to get user.id
        db.session.add(user)
        db.session.flush()  # This will assign user.id before committing

        # If the role is 'Doctor', create a corresponding Doctor instance
        if data['role'] == Role.DOCTOR.value:
            doctor = Doctor(
                userId=user.id
            )
            db.session.add(doctor)
            db.session.flush()  # Flush again to get doctor.id

            # Set doctorId in the User model
            user.doctorId = doctor.id

        # Commit both user and doctor (if applicable) to the database
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while creating the user", "error": str(e)}), 500

    return jsonify({"message": "User created successfully"}), 201

# login auth
@main.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if user and user.check_password(data['password']):
        # Initialize the payload for JWT
        identity = {
            'id': user.id,
            'role': user.role,
            'email': user.email
        }

        # If the user is a doctor, add the doctorId to the token
        if user.role == Role.DOCTOR.value:
            doctor = Doctor.query.filter_by(userId=user.id).first()
            if doctor:
                identity['doctorId'] = doctor.id

        # Create access token with custom expiration
        access_token = create_access_token(
            identity=identity,
            expires_delta=timedelta(days=7)  # Token expires in 7 days
        )

        # Return user details along with the access token
        response = {
            'token': access_token,
            'id': user.id,
            'email': user.email,
            'firstName': user.firstName,
            'lastName': user.lastName,
            'profilePic': user.profilePic,
            'contactNum': user.contactNum,
            'age': user.age,
            'gender': user.gender,
            'role': user.role
        }

        # If the user is a doctor, include the doctorId in the response
        if user.role == Role.DOCTOR.value and doctor:
            response['doctorId'] = doctor.id

        return jsonify(response), 200

    return jsonify({"message": "Invalid credentials"}), 401

# User detail
@main.route('/api/auth/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    if user:
        return jsonify({
            'id': user.id,
            'email': user.email,
            'firstName': user.firstName,
            'lastName': user.lastName,
            'profilePic': user.profilePic,
            'contactNum': user.contactNum,
            'age': user.age,
            'gender': user.gender,
            'role': user.role
        }), 200
    return jsonify({"message": "User not found"}), 404


# Create appointment
@main.route('/api/appointment', methods=['POST'])
@jwt_required()
def create_appointment():
    data = request.get_json()

    required_fields = ['doctorId', 'date', 'title']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400

    try:
     # Expecting date in the format 'YYYY-MM-DD'
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Use 'YYYY-MM-DD'"}), 400

    doctor = Doctor.query.get(data['doctorId'])
    if not doctor:
        return jsonify({"message": "Doctor not found"}), 404

    # Create an appointment
    appointment = Appointment(
        doctorId=data['doctorId'],
        date=appointment_date,
        title=data.get('title', '')  
    )

    try:
        db.session.add(appointment)
        db.session.commit()
        return jsonify({"message": "Appointment created successfully", "appointmentId": appointment.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating appointment", "error": str(e)}), 500


# View All appointments
@main.route('/api/appointment', methods=['GET'])
def view_appointments():
    appointments = Appointment.query.all()
    
    appointments_list = []
    for appointment in appointments:
        appointments_list.append({
            'id': appointment.id,
            'doctorId': appointment.doctorId,
            'date': appointment.date.strftime('%Y-%m-%d %H:%M:%S'),
            'title': appointment.title,
            'time': appointment.time.strftime('%H:%M:%S')
        })
    
    return jsonify({"appointments": appointments_list}), 200

