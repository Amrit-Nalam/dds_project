from flask import Blueprint, redirect, render_template, request, jsonify, url_for
from flask_login import login_required, current_user, logout_user
from app import db, socketio
from app.models import Customer, Order, Vendor, Ratings, Menu

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/vendors', methods=['GET'])
@login_required
def list_vendors():
    """Retrieve a list of vendors with their ratings and reviews."""
    location = request.args.get('location')
    min_rating = request.args.get('min_rating')
    vendor_name = request.args.get('vendor_name')

    query = Vendor.query

    if location:
        query = query.filter(Vendor.Location.ilike(f"%{location}%"))
    if min_rating:
        query = query.join(Ratings).group_by(Vendor.VendorID).having(db.func.avg(Ratings.Stars) >= float(min_rating))
    if vendor_name:
        query = query.filter(Vendor.VendorName.ilike(f"%{vendor_name}%"))

    vendors = query.all()

    result = []
    for vendor in vendors:
        avg_rating = db.session.query(db.func.avg(Ratings.Stars)).filter(Ratings.VendorID == vendor.VendorID).scalar()
        avg_rating = round(avg_rating, 2) if avg_rating else None

        reviews = Ratings.query.filter_by(VendorID=vendor.VendorID).all()
        reviews_list = [
            {
                "CustomerName": r.customer.CustomerName,
                "Stars": r.Stars,
                "Description": r.Description
            }
            for r in reviews
        ]

        menu_items = Menu.query.filter_by(VendorID=vendor.VendorID).all()
        menu_list = [{"MenuID": m.MenuID, "FoodItem": m.FoodItem, "Price": str(m.Price)} for m in menu_items]

        result.append({
            "VendorID": vendor.VendorID,
            "VendorName": vendor.VendorName,
            "Location": vendor.Location,
            "Phone": vendor.Phone,
            "Email": vendor.Email,
            "Address": vendor.Address,
            "avg_rating": avg_rating,
            "Reviews": reviews_list,
            "Menu": menu_list
        })

    return jsonify(result), 200

@customer_bp.route('/orders', methods=['POST'])
@login_required
def place_order():
    """Place an order for multiple items from a single vendor."""
    if current_user.Role != 'Customer':
        return jsonify({"error": "Only customers can place orders."}), 403

    data = request.get_json()
    vendor_id = data.get('vendorID')
    items = data.get('items')

    if not vendor_id or not items:
        return jsonify({"error": "VendorID and items are required."}), 400

    # Validate all items belong to the same vendor
    for item in items:
        menu_item = Menu.query.filter_by(MenuID=item['menuID'], VendorID=vendor_id).first()
        if not menu_item:
            return jsonify({"error": f"Menu item {item['menuID']} does not belong to vendor {vendor_id}."}), 400

    total_price = sum(item['price'] * item['quantity'] for item in items)

    customer = Customer.query.filter_by(UserID=current_user.UserID).first()

    # Create a new order
    for item in items:
        order = Order(
            VendorID=vendor_id,
            CustomerID=customer.CustomerID,
            MenuID=item['menuID'],
            Quantity=item['quantity'],
            TotalPrice=item['price'] * item['quantity'],
            OrderStatus='Pending'
        )
        db.session.add(order)

    db.session.commit()

    # Notify the vendor
    socketio.emit(
        'new_order',
        {
            "VendorID": vendor_id,
            "Orders": [{"menuID": item['menuID'], "quantity": item['quantity'], "price": item['price']} for item in items],
            "TotalPrice": total_price
        },
        to=f'vendor_{vendor_id}'
    )

    return jsonify({"message": "Order placed successfully."}), 201

@customer_bp.route('/orders/customer', methods=['GET'])
@login_required
def get_customer_orders():
    """Retrieve all orders placed by the logged-in customer."""
    if current_user.Role != 'Customer':
        return jsonify({"error": "Access denied. Only customers can view orders."}), 403

    customer = Customer.query.filter_by(UserID=current_user.UserID).first()
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    orders = Order.query.filter_by(CustomerID=customer.CustomerID).all()
    order_list = [
        {
            "OrderID": order.OrderID,
            "MenuItem": Menu.query.get(order.MenuID).FoodItem,
            "Quantity": order.Quantity,
            "TotalPrice": str(order.TotalPrice),
            "OrderStatus": order.OrderStatus,
            "OrderDate": order.OrderDate.strftime('%Y-%m-%d %H:%M:%S')
        }
        for order in orders
    ]

    return jsonify(order_list), 200

@customer_bp.route('/vendors/<int:vendor_id>/review', methods=['POST'])
@login_required
def add_review(vendor_id):
    """Add a rating and review for a vendor."""
    if current_user.Role != 'Customer':
        return jsonify({"error": "Only customers can add reviews."}), 403

    customer = Customer.query.filter_by(UserID=current_user.UserID).first()
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json()
    stars = data.get('Stars')
    description = data.get('Description')

    # Validate stars and description
    if not stars or not (1 <= int(stars) <= 5):
        return jsonify({"error": "Stars must be between 1 and 5."}), 400

    if not description or description.strip() == "":
        return jsonify({"error": "Description is required."}), 400

    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    # Check if the customer has already reviewed this vendor
    existing_review = Ratings.query.filter_by(CustomerID=customer.CustomerID, VendorID=vendor_id).first()
    if existing_review:
        return jsonify({"error": "You have already reviewed this vendor."}), 400

    # Add a new review
    new_review = Ratings(
        VendorID=vendor_id,
        CustomerID=customer.CustomerID,
        Stars=stars,
        Description=description.strip()
    )
    db.session.add(new_review)
    db.session.commit()

    # Return the updated average rating
    avg_rating = db.session.query(db.func.avg(Ratings.Stars)).filter(Ratings.VendorID == vendor_id).scalar()
    avg_rating = round(avg_rating, 2) if avg_rating else None

    return jsonify({
        "message": "Review added successfully.",
        "avg_rating": avg_rating
    }), 201


@customer_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Log the user out and redirect to the home page."""
    logout_user()  # Flask-Login function to log out the user
    return render_template('index.html')  # Redirect to the homepage
