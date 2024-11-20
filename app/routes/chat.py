from flask import Blueprint, render_template, request, session
from flask_socketio import emit
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")
chat_bp = Blueprint('chat', __name__)

users = {}

@socketio.on("connect")
def handle_connect():
    print("Client connected!")

@socketio.on("user_join")
def handle_user_join(username):
    #username = data.get("username")
    print(f"User {username} joined!")
    users[username] = request.sid

@socketio.on("new_message")
def handle_new_message(message):
    print(f"New message: {message}")
    username = None 
    for user in users:
        if users[user] == request.sid:
            username = user
    emit("chat", {"message": message, "username": username}, broadcast=True)

@chat_bp.route("/chat")
def chat():
    username = request.args.get('username', 'Anonymous')
    return render_template("chat.html", username=username)
