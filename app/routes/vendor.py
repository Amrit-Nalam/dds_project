from flask import Blueprint, redirect, render_template, request, jsonify, url_for
from app import db, socketio
from app.models import Customer, Menu, AuthUser, Order, Vendor
from flask_socketio import emit

vendor_bp = Blueprint('vendor', __name__)

def validate_vendor(user_id):
    """Validate that the user is a vendor and exists in the Vendor table."""
    vendor = Vendor.query.filter_by(UserID=user_id).first()
    if not vendor:
        return None, jsonify({"error": "Access denied. Vendor does not exist"}), 403
    return vendor, None


from flask_login import UserMixin, current_user, login_required, logout_user

class MockVendor(UserMixin):
    def __init__(self):
        self.Role = "Vendor"
        self.UserID = 11

@vendor_bp.route('/menu', methods=['GET'])
#@login_required
def get_menu_items():
    """Retrieve all menu items for the logged-in vendor."""
    current_user = MockVendor()
    # if current_user.Role != 'Vendor':
    #     return jsonify({"error": "Access denied. Only vendors can view menu items."}), 403

    # Get the vendor ID from the current user's UserID
    vendor = Vendor.query.filter_by(UserID=current_user.UserID).first()
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    # Fetch menu items
    menu_items = Menu.query.filter_by(VendorID=vendor.VendorID).all()
    menu_list = [
        {"MenuID": item.MenuID, "FoodItem": item.FoodItem, "Price": str(item.Price), "Description": item.Description}
        for item in menu_items
    ]

    return jsonify({"menu": menu_list}), 200


@vendor_bp.route('/menu', methods=['POST'])
@login_required
def add_menu_item():
    """Add a new menu item for the logged-in vendor."""
    if current_user.Role != 'Vendor':
        return jsonify({"error": "Access denied. Only vendors can add menu items."}), 403

    # Get the vendor ID from the current user's UserID
    vendor = Vendor.query.filter_by(UserID=current_user.UserID).first()
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    data = request.get_json()
    food_item = data.get('FoodItem')
    price = data.get('Price')
    description = data.get('Description', '')

    if not food_item or not price:
        return jsonify({"error": "FoodItem and Price are required"}), 400

    # Add the menu item
    new_menu_item = Menu(
        VendorID=vendor.VendorID,
        FoodItem=food_item,
        Price=price,
        Description=description
    )
    db.session.add(new_menu_item)
    db.session.commit()

    return jsonify({"message": "Menu item added successfully"}), 201


from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Menu, Vendor

vendor_bp = Blueprint('vendor', __name__)

@vendor_bp.route('/menu', methods=['GET'])
#@login_required
def get_menu_items():
    """Retrieve all menu items for the logged-in vendor."""
    current_user = MockVendor()
    # if current_user.Role != 'Vendor':
    #     return jsonify({"error": "Access denied. Only vendors can view menu items."}), 403

    # Get the vendor ID from the current user's UserID
    vendor = Vendor.query.filter_by(UserID=current_user.UserID).first()
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    # Fetch menu items
    menu_items = Menu.query.filter_by(VendorID=vendor.VendorID).all()
    menu_list = [
        {"MenuID": item.MenuID, "FoodItem": item.FoodItem, "Price": str(item.Price), "Description": item.Description}
        for item in menu_items
    ]

    return jsonify({"menu": menu_list}), 200

@vendor_bp.route('/menu', methods=['POST'])
@login_required
def add_menu_item():
    """Add a new menu item for the logged-in vendor."""
    if current_user.Role != 'Vendor':
        return jsonify({"error": "Access denied. Only vendors can add menu items."}), 403

    vendor = Vendor.query.filter_by(UserID=current_user.UserID).first()
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    data = request.get_json()
    food_item = data.get('FoodItem')
    price = data.get('Price')
    description = data.get('Description', '')

    if not food_item or not price:
        return jsonify({"error": "FoodItem and Price are required"}), 400

    new_menu_item = Menu(
        VendorID=vendor.VendorID,
        FoodItem=food_item,
        Price=price,
        Description=description
    )
    db.session.add(new_menu_item)
    db.session.commit()

    return jsonify({"message": "Menu item added successfully"}), 201

@vendor_bp.route('/menu/<int:menu_id>', methods=['PUT'])
@login_required
def update_menu_item(menu_id):
    """Update an existing menu item."""
    if current_user.Role != 'Vendor':
        return jsonify({"error": "Access denied. Only vendors can update menu items."}), 403

    vendor = Vendor.query.filter_by(UserID=current_user.UserID).first()
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    menu_item = Menu.query.filter_by(MenuID=menu_id, VendorID=vendor.VendorID).first()
    if not menu_item:
        return jsonify({"error": "Menu item not found or access denied"}), 404

    data = request.get_json()
    menu_item.FoodItem = data.get('FoodItem', menu_item.FoodItem)
    menu_item.Price = data.get('Price', menu_item.Price)
    menu_item.Description = data.get('Description', menu_item.Description)

    db.session.commit()

    return jsonify({"message": "Menu item updated successfully"}), 200

@vendor_bp.route('/orders', methods=['GET'])
@login_required
def get_vendor_orders():
    """Retrieve all orders for the vendor."""
    if current_user.Role != 'Vendor':
        return jsonify({"error": "Access denied. Only vendors can view orders."}), 403

    vendor = Vendor.query.filter_by(UserID=current_user.UserID).first()
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    # Fetch orders with customer details
    orders = db.session.query(Order, Customer).join(Customer, Order.CustomerID == Customer.CustomerID).filter(
        Order.VendorID == vendor.VendorID).order_by(Order.OrderDate.desc()).all()

    order_list = [
        {
            "OrderID": o.Order.OrderID,
            "MenuItem": o.Order.menu.FoodItem,
            "Quantity": o.Order.Quantity,
            "TotalPrice": str(o.Order.TotalPrice),
            "OrderStatus": o.Order.OrderStatus,
            "OrderDate": o.Order.OrderDate.strftime('%Y-%m-%d %H:%M:%S'),
            "CustomerName": o.Customer.CustomerName,  # Customer's name
            "CustomerLocation": o.Customer.Location  # Optional, e.g., customer's location
        }
        for o in orders
    ]

    return jsonify({"orders": order_list}), 200

@vendor_bp.route("/chat/rooms", methods=["GET"])
@login_required
def get_vendor_chat_rooms():
    """Fetch chat rooms for the logged-in vendor."""
    if current_user.Role != "Vendor":
        return jsonify({"error": "Access denied. Only vendors can access this."}), 403

    # Fetch vendor details
    vendor = Vendor.query.filter_by(UserID=current_user.UserID).first()
    if not vendor:
        return jsonify({"error": "Vendor not found."}), 404

    # Fetch orders and create chat rooms based on customer IDs
    orders = Order.query.filter_by(VendorID=vendor.VendorID).all()
    rooms = [f"room_{vendor.VendorID}_{order.CustomerID}" for order in orders]

    return jsonify({"rooms": rooms}), 200


@vendor_bp.route('/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order_status(order_id):
    """Update the status of an order."""
    if current_user.Role != 'Vendor':
        return jsonify({"error": "Access denied. Only vendors can update orders."}), 403

    data = request.get_json()
    new_status = data.get('OrderStatus')

    if new_status not in ['Pending', 'Completed', 'Cancelled']:
        return jsonify({"error": "Invalid order status."}), 400

    order = Order.query.filter_by(OrderID=order_id, VendorID=current_user.vendor.VendorID).first()
    if not order:
        return jsonify({"error": "Order not found or access denied."}), 404

    order.OrderStatus = new_status
    db.session.commit()

    # Notify the customer
    socketio.emit('order_status_update', {
        "OrderID": order.OrderID,
        "NewStatus": new_status,
        "CustomerName": order.customer.CustomerName
    }, to="customers")

    return jsonify({"message": "Order status updated successfully."}), 200

@vendor_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Log the user out and redirect to the home page."""
    logout_user()  # Flask-Login function to log out the user
    return render_template('index.html')  # Redirect to the homepage




