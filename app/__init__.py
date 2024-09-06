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
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:admin@localhost:5432/ehr"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "b52264934f8dc66bba2a9f9b28871d0993a728f0be4ab165ab4b034af3219184"
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7) 

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app
