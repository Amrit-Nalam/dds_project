from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO
from sqlalchemy.orm import configure_mappers

socketio = SocketIO(cors_allowed_origins="*")
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    configure_mappers()
    socketio.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.vendor import vendor_bp
    from app.routes.customer import customer_bp
    from app.routes.chat import chat_bp
    app.register_blueprint(auth_bp)  
    app.register_blueprint(vendor_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(chat_bp)
    return app