from datetime import datetime, timedelta
from functools import wraps
import uuid
from flask import Blueprint, app, request, jsonify
from flask_jwt_extended import create_access_token, get_current_user, get_jwt_identity, jwt_required
from app import db
from app.models import Appointment, Gender, Role, User, Doctor, Admin, Patient
from werkzeug.exceptions import BadRequest

main = Blueprint('main', __name__)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        if current_user['role'] != Role.ADMIN.value:
            return jsonify({"message": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


# Registration Auth
@main.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate incoming data
    required_fields = ['email', 'password', 'firstName', 'lastName', 'gender', 'dateOfBirth', 'age', 'contactNum', 'profilePic', 'role']
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
        dateOfBirth=data['dateOfBirth'],
        age=data['age'],
        gender=data['gender'],
        contactNum=data['contactNum'],
        profilePic=data['profilePic'],
        role=data['role']
    )
    user.set_password(data['password'])  # Hash the password

    try:
        db.session.add(user)
        db.session.flush()  

        # If the role is 'Doctor', create a corresponding Doctor instance
        if data['role'] == Role.DOCTOR.value:
            doctor = Doctor(
                userId=user.id  
            )
            db.session.add(doctor)
            db.session.flush()

            # Set doctorId in the User model
            user.doctorId = doctor.id

        # If the role is 'Admin', create a corresponding Admin instance
        elif data['role'] == Role.ADMIN.value:
            admin = Admin(
                userId=user.id  
            )
            db.session.add(admin)
            db.session.flush()
            
            user.adminId = admin.id

        # If the role is 'Patient', create a corresponding Patient instance
        elif data['role'] == Role.PATIENT.value:
            patient = Patient(
                userId=user.id  
            )
            db.session.add(patient)
            db.session.flush()
            
            user.patientId = patient.id


        # Commit after all related instances are set
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
            'dateOfBirth': user.dateOfBirth,
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



# User deatil
@main.route('/api/auth/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    
    if user:
        user_data = {
            'id': user.id,
            'email': user.email,
            'firstName': user.firstName,
            'lastName': user.lastName,
            'dateOfBirth': user.dateOfBirth,
            'profilePic': user.profilePic,
            'contactNum': user.contactNum,
            'age': user.age,
            'gender': user.gender,
            'role': user.role
        }
        
        # If user is doctor, return doctorId in response
        if user.role == Role.DOCTOR.value:
            doctor = Doctor.query.filter_by(userId=user.id).first()
            if doctor:
                user_data['doctorId'] = doctor.id

        return jsonify(user_data), 200
    
    return jsonify({"message": "User not found"}), 404



# update user data 
@main.route('/api/auth/user/<uuid:user_id>', methods=['PATCH'])
@jwt_required()
@admin_required
def update_user(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    try:
        # Update user details
        if 'email' in data:
            user.email = data['email']
        if 'firstName' in data:
            user.firstName = data['firstName']
        if 'lastName' in data:
            user.lastName = data['lastName']
        if 'dateOfBirth' in data:
            user.dateOfBirth = data['dateOfBirth']
        if 'age' in data:
            user.age = data['age']
        if 'gender' in data:
            user.gender = data['gender']
        if 'contactNum' in data:
            user.contactNum = data['contactNum']
        if 'profilePic' in data:
            user.profilePic = data['profilePic']
        if 'role' in data:
            if data['role'] not in [role.value for role in Role]:
                return jsonify({'message': 'Invalid role'}), 400
            user.role = data['role']
        
        if 'password' in data:
            user.set_password(data['password'])

        db.session.commit()

        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while updating the user', 'error': str(e)}), 500


# Delete user by id
@main.route('/api/auth/user/<uuid:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    try:
        # Delete related records
        Doctor.query.filter_by(userId=user_id).delete()
        Patient.query.filter_by(userId=user_id).delete()
        Admin.query.filter_by(userId=user_id).delete()

        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while deleting the user', 'error': str(e)}), 500


# Create appointment
@main.route('/api/appointment', methods=['POST'])
@jwt_required()
def create_appointment():
    data = request.get_json()
    current_user = get_jwt_identity()

    required_fields = ['doctorId', 'date', 'title', 'time', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400

    try:
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Use 'YYYY-MM-DD'"}), 400

    try:
        appointment_time = datetime.strptime(data['time'], '%H:%M').time()
    except ValueError:
        return jsonify({"message": "Invalid time format. Use 'HH:MM'"}), 400

    doctor = Doctor.query.get(data['doctorId'])
    if not doctor:
        return jsonify({"message": "Doctor not found"}), 404

    user = User.query.get(current_user['id'])
    
    if user.role == Role.ADMIN.value:
        # Admin can create appointments for any doctor
        appointment = Appointment(
            doctorId=data['doctorId'],
            date=appointment_date,
            title=data.get('title', ''),
            time=appointment_time,
            price=data.get('price')
        )
    elif user.role == Role.DOCTOR.value:
        # Doctors can only create appointments for themselves
        if doctor.id != user.doctorId:
            return jsonify({"message": "You can only create appointments for yourself."}), 403
        appointment = Appointment(
            doctorId=user.doctorId,
            date=appointment_date,
            title=data.get('title', ''),
            time=appointment_time,
            price=data.get('price'),
        )
    else:
        return jsonify({"message": "Unauthorized user role."}), 403

    try:
        db.session.add(appointment)
        db.session.commit()
        
        response = {
            "message": "Appointment created successfully",
            "appointment": {
                'id': appointment.id,
                'doctorId': appointment.doctorId,
                'date': appointment.date.strftime('%Y-%m-%d'),
                'title': appointment.title,
                'time': appointment.time.strftime('%H:%M'),
                'price': appointment.price
            }
        }
        return jsonify(response), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating appointment", "error": str(e)}), 500




# View All appointments
@main.route('/api/appointment', methods=['GET'])
@jwt_required()
def view_appointments():
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])

    if user.role == Role.ADMIN.value:
        appointments = Appointment.query.all()
    elif user.role == Role.DOCTOR.value:
        appointments = Appointment.query.filter_by(doctorId=user.doctorId).all()
    else:
        return jsonify({"message": "Unauthorized user role."}), 403

    appointments_list = []
    for appointment in appointments:
        # Fetch the user (patient) who matches the patientId in the appointment
        patient_user = appointment.patient
        if patient_user is None:
            appointments_list.append({
                'id': appointment.id,
                'doctorId': appointment.doctorId,
                'date': appointment.date.strftime('%Y-%m-%d'),
                'title': appointment.title,
                'time': appointment.time.strftime('%H:%M'),
                'user': {
                    # No patient user details available
                }
            })
        else:
            # Access user details through the relationship
            appointments_list.append({
                'id': appointment.id,
                'doctorId': appointment.doctorId,
                'date': appointment.date.strftime('%Y-%m-%d'),
                'title': appointment.title,
                'time': appointment.time.strftime('%H:%M'),
                'user': {
                    'id': patient_user.user.id,
                    'firstName': patient_user.user.firstName,
                    'lastName': patient_user.user.lastName,
                    'dateOfBirth': patient_user.user.dateOfBirth,
                    'email': patient_user.user.email,
                    'contactNum': patient_user.user.contactNum,
                    'age': patient_user.user.age,
                    'gender': patient_user.user.gender
                }
            })

    return jsonify(appointments_list), 200



# View appointment by date
@main.route('/api/appointment/date', methods=['POST'])
def get_appointments_by_date():
    # Extract data from JSON body
    data = request.get_json()
    
    # Check if 'date' is provided
    if not data or 'date' not in data:
        return jsonify({"message": "Date is required"}), 400
    
    date_str = data['date']
    
    try:
        # Convert string to date
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Query appointments by date using SQLAlchemy ORM
    appointments = Appointment.query.filter_by(date=appointment_date).all()

    if not appointments:
        return jsonify({"message": "No appointments found for this date."}), 404

    # Prepare the appointments data to return
    appointments_data = [
        {
            'id': str(appointment.id),
            'doctorId': str(appointment.doctorId),
            'patientId': str(appointment.patientId),
            'date': appointment.date.strftime('%Y-%m-%d'),
            'title': appointment.title,
            'notes': appointment.notes,
            'time': appointment.time.strftime('%H:%M'),
            'createdAt': appointment.createdAt.strftime('%Y-%m-%d %H:%M:%S') if appointment.createdAt else None,
            'updatedAt': appointment.updatedAt.strftime('%Y-%m-%d %H:%M:%S') if appointment.updatedAt else None,

        }
        for appointment in appointments
    ]

    return jsonify(appointments_data), 200


# View appointment by ID
@main.route('/api/appointment/<appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({"message": "Appointment not found"}), 404

    if user.role == Role.ADMIN.value or (user.role == Role.DOCTOR.value and appointment.doctorId == user.doctorId):
        return jsonify({
            'id': appointment.id,
            'doctorId': appointment.doctorId,
            'date': appointment.date.strftime('%Y-%m-%d'),
            'title': appointment.title,
            'time': appointment.time.strftime('%H:%M')
        }), 200
    else:
        return jsonify({"message": "Unauthorized to access this appointment."}), 403



# Delete appointment by ID
@main.route('/api/appointment/<appointment_id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(appointment_id):
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({"message": "Appointment not found"}), 404

    if user.role == Role.ADMIN.value or (user.role == Role.DOCTOR.value and appointment.doctorId == user.doctorId):
        try:
            db.session.delete(appointment)
            db.session.commit()
            return jsonify({"message": "Appointment deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Error deleting appointment", "error": str(e)}), 500
    else:
        return jsonify({"message": "Unauthorized to delete this appointment."}), 403




# Update appointments by ID
@main.route('/api/appointment/<appointment_id>', methods=['PATCH'])
@jwt_required()
def update_appointment(appointment_id):
    data = request.get_json()
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({"message": "Appointment not found. Please check the appointment ID and try again.", 'statusCode': 404,}), 404

    if not (user.role == Role.ADMIN.value or (user.role == Role.DOCTOR.value and appointment.doctorId == user.doctorId)):
        return jsonify({"message": "Unauthorized to update this appointment. You may not have the necessary permissions.", 'statusCode': 403,}), 403

    # Update appointment details
    updated = False

    if 'date' in data:
        try:
            appointment.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            updated = True
        except ValueError:
            return jsonify({"message": "Invalid date format. Please use 'YYYY-MM-DD'.", 'statusCode': 400,}), 400
        
    if 'time' in data:
        try:
            appointment.time = datetime.strptime(data['time'], '%H:%M').time()
            updated = True
        except ValueError:
            return jsonify({"message": "Invalid time format. Please use 'HH:MM'.", 'statusCode': 400,}), 400
        
    if 'title' in data:
        appointment.title = data['title']
        updated = True

    if not updated:
        return jsonify({"message": "No update parameters provided. Please include 'date', 'time', or 'title' to update.", 
                        'statusCode': 400,}), 400

    try:
        db.session.commit()
        return jsonify({
            'message': 'Appointment updated successfully.',
            'statusCode': 200,
            'appointment': {
                'id': appointment.id,
                'doctorId': appointment.doctorId,
                'date': appointment.date.strftime('%Y-%m-%d'),
                'title': appointment.title,
                'time': appointment.time.strftime('%H:%M:%S')
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating the appointment. Please try again later.", "error": str(e), 'statusCode': 500,}), 500
