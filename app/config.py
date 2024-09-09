import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url= os.environ.get("SUPABASE_URL")
key= os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)


# class Config:
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  
