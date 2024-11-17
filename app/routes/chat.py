from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import socketio, db
from flask_socketio import emit, join_room, leave_room
from app.models import Vendor, Customer, AuthUser

chat_bp = Blueprint('chat', __name__)

@socketio.on('connect')
def connect():
    token = request.args.get('token')
    user = AuthUser.query.filter_by(UserID=token).first()

    if not user:
        return False  # Reject the connection if the user is not authenticated

    # Store user info in the session for WebSocket
    request.environ['user'] = user
    print(f"User {user.Username} connected.")

@socketio.on('join_room')
def handle_join(data):
    room = "global_chat"  # Single global room for everyone
    join_room(room)
    username = data.get('username', 'Anonymous')
    print(f"{username} joined the room: {room}")
    emit('message', {'user': 'System', 'msg': f'{username} has joined the chat.'}, room=room)


@socketio.on('leave_room')
def handle_leave(data):
    room = "global_chat"
    username = data.get('username', 'Anonymous')
    leave_room(room)
    emit('message', {'user': 'System', 'msg': f'{username} has left the chat.'}, room=room)

@socketio.on('send_message')
def handle_send_message(data):
    room = "global_chat"
    username = data.get('username', 'Anonymous')
    message = data.get('message', '')
    print(f"Message received: {message} from {username} in room {room}")
    emit('message', {'user': username, 'msg': message}, room=room)


@chat_bp.route('/chat/rooms', methods=['GET'])
@login_required
def get_chat_rooms():
    """Get available chat rooms."""
    try:
        if current_user.Role == 'Customer':
            rooms = Vendor.query.with_entities(Vendor.VendorID, Vendor.VendorName).all()
        elif current_user.Role == 'Vendor':
            rooms = Customer.query.with_entities(Customer.CustomerID, Customer.CustomerName).all()
        else:
            return jsonify({"error": "Invalid role"}), 403

        return jsonify([{"id": room[0], "name": room[1]} for room in rooms]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
