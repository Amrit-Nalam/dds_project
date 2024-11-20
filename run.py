from app import create_app, socketio
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables in the database
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
