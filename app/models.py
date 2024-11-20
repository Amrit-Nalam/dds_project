from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

#db = SQLAlchemy()

class AuthUser(db.Model, UserMixin):
    __tablename__ = 'AuthUser'
    UserID = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(50), unique=True, nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    Role = db.Column(db.Enum('Customer', 'Vendor'), nullable=False)
    CreatedAt = db.Column(db.DateTime, server_default=db.func.now())

    def get_id(self):
        return str(self.UserID)
    customer = db.relationship('Customer', backref='auth_user', uselist=False)
    vendor = db.relationship('Vendor', backref='auth_user', uselist=False)

class Vendor(db.Model):
    __tablename__ = 'Vendor'
    VendorID = db.Column(db.Integer, primary_key=True)
    VendorName = db.Column(db.String(100), nullable=False)
    Phone = db.Column(db.String(15), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    Address = db.Column(db.String(255))
    Location = db.Column(db.String(100))
    UserID = db.Column(db.Integer, db.ForeignKey('AuthUser.UserID', ondelete="CASCADE"), nullable=False)
    menu_items = db.relationship('Menu', back_populates='vendor', cascade="all, delete-orphan")

class Customer(db.Model):
    __tablename__ = 'Customer'
    CustomerID = db.Column(db.Integer, primary_key=True)
    CustomerName = db.Column(db.String(100), nullable=False)
    Phone = db.Column(db.String(15), nullable=False)
    Location = db.Column(db.String(100))
    UserID = db.Column(db.Integer, db.ForeignKey('AuthUser.UserID', ondelete="CASCADE"), nullable=False)
    orders = db.relationship('Order', back_populates='customer', cascade="all, delete-orphan")

class Ratings(db.Model):
    __tablename__ = 'Ratings'
    RatingID = db.Column(db.Integer, primary_key=True)
    VendorID = db.Column(db.Integer, db.ForeignKey('Vendor.VendorID', ondelete="CASCADE"), nullable=False)
    CustomerID = db.Column(db.Integer, db.ForeignKey('Customer.CustomerID', ondelete="CASCADE"), nullable=False)
    Stars = db.Column(db.Integer, nullable=False)  # 1 to 5
    Description = db.Column(db.Text)

    # Relationship to Customer
    customer = db.relationship('Customer', backref='ratings')
    vendor = db.relationship('Vendor', backref='ratings')


class Menu(db.Model):
    __tablename__ = 'Menu'
    MenuID = db.Column(db.Integer, primary_key=True)
    VendorID = db.Column(db.Integer, db.ForeignKey('Vendor.VendorID', ondelete="CASCADE"), nullable=False)
    FoodItem = db.Column(db.String(100), nullable=False)
    Price = db.Column(db.Numeric(10, 2), nullable=False)
    Description = db.Column(db.Text)
    orders = db.relationship('Order', backref='menu', lazy=True)
    vendor = db.relationship('Vendor', back_populates='menu_items')  # Vendor relationship
    orders = db.relationship('Order', back_populates='menu', cascade="all, delete-orphan")

class Order(db.Model):
    __tablename__ = 'Order'
    OrderID = db.Column(db.Integer, primary_key=True)
    VendorID = db.Column(db.Integer, db.ForeignKey('Vendor.VendorID', ondelete="CASCADE"), nullable=False)
    CustomerID = db.Column(db.Integer, db.ForeignKey('Customer.CustomerID', ondelete="CASCADE"), nullable=False)
    MenuID = db.Column(db.Integer, db.ForeignKey('Menu.MenuID', ondelete="CASCADE"), nullable=False)
    OrderDate = db.Column(db.DateTime, server_default=db.func.now())
    OrderStatus = db.Column(db.Enum('Pending', 'Completed', 'Cancelled'), default='Pending')
    Quantity = db.Column(db.Integer, nullable=False)
    TotalPrice = db.Column(db.Numeric(10, 2), nullable=False)

    customer = db.relationship('Customer', back_populates='orders')
    menu = db.relationship('Menu', back_populates='orders')
