from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User

main = Blueprint('main', __name__)

@main.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        # profile_pic=data.get('profile_pic', ''),
        role=data.get('role', '')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@main.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity={'id': user.id, 'role': user.role, 'email': user.email})
        return jsonify(access_token=access_token), 200
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
            'first_name': user.first_name,
            'last_name': user.last_name,
            # 'profile_pic': user.profile_pic,
            'role': user.role
        }), 200
    return jsonify({"message": "User not found"}), 404
