import uuid
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UUID, Enum
from enum import Enum as PyEnum
from datetime import datetime
from . import db

bcrypt = Bcrypt()

class Role(PyEnum):
    DOCTOR = 'Doctor'
    ADMIN = 'Admin'
    PATIENT = 'Patient'
    
class Gender(PyEnum):
    MALE = 'Male'
    FEMALE = 'Female'
    


class User(db.Model):
    # __tablename__ = 'Users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    doctorId = db.Column(UUID(as_uuid=True), nullable=True)
    adminId = db.Column(UUID(as_uuid=True), nullable=True)
    patientId = db.Column(UUID(as_uuid=True), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    firstName = db.Column(db.String(255), nullable=False)
    lastName = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    dateOfBirth = db.Column(db.Date, nullable=True)  
    gender = db.Column(db.String(10), nullable=True)
    contactNum = db.Column(db.String(15), nullable=True)
    profilePic = db.Column(db.String(255), nullable=True)  # URL as a string
    role = db.Column(db.String(10), nullable=False)
    isAdmin = db.Column(db.Boolean, default=False)
    createdAt = db.Column(db.DateTime, default=datetime.now)
    updatedAt = db.Column(db.DateTime, onupdate=datetime.now)
    
    patient = db.relationship('Patient', back_populates='user', uselist=False, cascade="all, delete-orphan")
    doctor = db.relationship('Doctor', back_populates='user', uselist=False, cascade="all, delete-orphan")
    admin = db.relationship('Admin', back_populates='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


    def __repr__(self):
        return f'<User {self.email}>'
    
    
class Doctor(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    userId = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    specialization = db.Column(db.String(255), nullable=True) 
    experience = db.Column(db.Integer, nullable=True)  
    availability = db.Column(db.String(255), nullable=True) 
    
    # Relationship to the User model
    user = db.relationship('User', back_populates='doctor')

    def __repr__(self):
        return f'<Doctor {self.id}>'


class Appointment(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    doctorId = db.Column(UUID(as_uuid=True), db.ForeignKey('doctor.id'), nullable=False)
    patientId = db.Column(UUID(as_uuid=True), db.ForeignKey('patient.id'), nullable=True)  # Ensure this matches your DB schema
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=True)     
    time = db.Column(db.Time, default=datetime.now().time(), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.now)
    updatedAt = db.Column(db.DateTime, onupdate=datetime.now)
    
    # Relationships
    doctor = db.relationship('Doctor', backref=db.backref('appointments'))
    patient = db.relationship('Patient', backref=db.backref('appointments'))



class Patient(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    userId = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    
    # Relationship to the User model
    user = db.relationship('User', back_populates='patient')

    def __repr__(self):
        return f'<Patient {self.id}>'

    
class Admin(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    userId = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    # appointmentId = db.Column(UUID(as_uuid=True), db.ForeignKey('appointment.id'), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.now)
    updatedAt = db.Column(db.DateTime, onupdate=datetime.now)  
    # Relationship to the User model
    user = db.relationship('User', back_populates='admin')

    def __repr__(self):
        return f'<Admin {self.user.email}>'
