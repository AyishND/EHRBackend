from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres.sfdnwvfubodahbhbynxl:BreakingBadSeason123@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "9TM5WVZ9yGqTRY4m6Imx9acbPPomyzGTB3zsGJ3fKxABOZN1ZtVwyqx//LG1x8WHxYtpWnjpyUp3o2xlnhWNCA=="
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7) 

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app
