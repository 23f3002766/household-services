from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# Comment Test 


# User Base Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin'

# Service Model
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.String(50), nullable=False)  # e.g., "2 hours"
    description = db.Column(db.Text, nullable=True)

# Service Professional Model
class ServiceProfessional(db.Model):
    __tablename__ = 'service_professionals'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now())
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False) 
    service_type = db.Column(db.String, nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(240), nullable=True)
    phone = db.Column(db.Integer, nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    pdf_path = db.Column(db.String(300), nullable=False)
    approved = db.Column(db.Boolean, default=False)  # Admin approval status
    blocked = db.Column(db.Boolean, default=False)  # Admin block status

# Customer Model
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(240), nullable=True)
    pincode = db.Column(db.Integer, nullable=False)

# Service Request Model
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'), nullable=True)
    date_of_request = db.Column(db.DateTime, default=datetime.now())
    date_of_completion = db.Column(db.DateTime, nullable=True)
    service_status = db.Column(db.String(20), default='requested')  # requested/assigned/closed
    remarks = db.Column(db.Text, nullable=True)

# Relationships
Service.professional = db.relationship('ServiceProfessional',cascade="all, delete", backref='services', lazy=True)
Service.service = db.relationship('ServiceRequest',cascade="all, delete", backref='services', lazy=True)
Customer.customer = db.relationship('ServiceRequest',cascade="all, delete", backref='customers', lazy=True)
ServiceProfessional.professional = db.relationship('ServiceRequest',cascade="all, delete", backref='service_professionals', lazy=True)
