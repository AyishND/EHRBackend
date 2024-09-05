from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app import db
from app.models import Gender, Role, User
from werkzeug.exceptions import BadRequest

main = Blueprint('main', __name__)

@main.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate incoming data
    required_fields = ['email', 'password','gender', 'age', 'contactNum', 'profilePic', 'role']
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
        return jsonify({"message": "Invalid role"}), 400
    
    
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

    # Add user to the database
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while creating the user", "error": str(e)}), 500

    # Optionally return a response success message
    return jsonify({"message": "User created successfully"}), 201


@main.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        # Create access token with custom expiration
        access_token = create_access_token(
            identity={'id': user.id, 'role': user.role, 'email': user.email},
            expires_delta=timedelta(days=7)  # Token expires in 30 minutes
        )

        return jsonify({
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
         }), 200
    return jsonify({"message": "Invalid credentials"}), 401

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
