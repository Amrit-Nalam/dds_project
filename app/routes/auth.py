from flask import Blueprint, request, jsonify, render_template
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt, login_manager
from app.models import AuthUser, Customer, Vendor

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return AuthUser.query.get(int(user_id))

@auth_bp.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET'])
def serve_register():
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET'])
def serve_login():
    return render_template('login.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    additional_data = data.get('additional_data', {})

    # Check if user already exists
    if AuthUser.query.filter((AuthUser.Username == username) | (AuthUser.Email == email)).first():
        return jsonify({"message": "Username or email already exists"}), 400

    # Hash the password
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create new user
    new_user = AuthUser(Username=username, Email=email, PasswordHash=password_hash, Role=role)
    db.session.add(new_user)
    db.session.flush()  # Retrieve UserID for customer/vendor creation

    # Create corresponding Customer or Vendor
    if role == 'Customer':
        new_customer = Customer(
            UserID=new_user.UserID,
            CustomerName=additional_data.get('customer_name', ''),
            Phone=additional_data.get('phone', ''),
            Location=additional_data.get('location', '')
        )
        db.session.add(new_customer)
    elif role == 'Vendor':
        new_vendor = Vendor(
            UserID=new_user.UserID,
            VendorName=additional_data.get('vendor_name', ''),
            Phone=additional_data.get('phone', ''),
            Email=email,
            Address=additional_data.get('address', ''),
            Location=additional_data.get('location', '')
        )
        db.session.add(new_vendor)

    db.session.commit()
    return jsonify({"message": f"{role} '{username}' registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data.get('username_or_email')
    password = data.get('password')
    role = data.get('role')  # Get role from the client

    user = AuthUser.query.filter(
        (AuthUser.Username == username_or_email) | (AuthUser.Email == username_or_email),
        AuthUser.Role == role  # Match the role
    ).first()

    if user and bcrypt.check_password_hash(user.PasswordHash, password):
        login_user(user)
        return jsonify({"message": f"{role} login successful"}), 200

    return jsonify({"message": "Invalid credentials or role mismatch"}), 401

@auth_bp.route('/customer_dashboard', methods=['GET'])
@login_required
def customer_dashboard():
    if current_user.Role != 'Customer':
        return render_template('error.html', error_message="Access Denied!"), 403
    return render_template('customer_dashboard.html', username=current_user.Username)


@auth_bp.route('/vendor_dashboard', methods=['GET'])
@login_required
def vendor_dashboard():
    if current_user.Role != 'Vendor':
        return render_template('error.html', error_message="Access Denied!"), 403
    return render_template('vendor_dashboard.html', current_user=current_user)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200
