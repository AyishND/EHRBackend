import os

class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:admin@localhost:5432/ehr_app_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'b52264934f8dc66bba2a9f9b28871d0993a728f0be4ab165ab4b034af3219184')  
