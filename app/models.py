import bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
from enum import Enum as PyEnum
from datetime import datetime

db = SQLAlchemy()

class Role(PyEnum):
    DOCTOR = 'Doctor'
    ADMIN = 'Admin'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    firstName = db.Column(db.String(255), nullable=False)
    lastName = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    contactNum = db.Column(db.String(15), nullable=True)
    profilePic = db.Column(db.String(255), nullable=True)  # URL as a string
    role = db.Column(Enum(Role), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.email}>'