#App routes
from flask import render_template,redirect,request,url_for
from app import app
from .models import db,User,ServiceProfessional,Customer

#Admin Routes
@app.route("/admin/login", methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('user_name')
        pwd = request.form.get('password')
        user = User.query.filter_by(username=user, password=pwd).first()
        print(user)
        if user and user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        print('Invalid credentials!')
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

#Customer Routes
@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('user_name')
        pwd = request.form.get('password')
        full_name = request.form.get('full_name')
        address = request.form.get('location')
        pin = request.form.get('pin_code')

        # Check if the username already exists
        if Customer.query.filter_by(username=user).first():
            print('Username already exists!', 'error')
            return render_template('signup.html',msg="Sorry, this mail already registered!!!")

        # Create Customer with user_id and service_id      
        new_customer = Customer(
            username=user, 
            password=pwd, 
            role='customer',
            name=full_name,
            address=address,
            pincode=int(pin),
        )
        db.session.add(new_customer)
        db.session.commit()       

        print(' Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template("signup.html")

@app.route("/", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('user_name')
        pwd = request.form.get('password')
        user = Customer.query.filter_by(username=user, password=pwd).first()
        if user and user.role == 'customer':
            return redirect(url_for('dashboard',name=user.name,id=user.id))
        print('Invalid credentials!')
    return render_template("login.html")

@app.route("/dashboard/<id>/<name>")
def dashboard(id,name):
    return render_template("dashboard.html",name=name,id=id)

@app.route("/booking")
def booking():
    return render_template("booking.html")

#Service Personal Routes
@app.route("/spsignup", methods = ['GET','POST'])
def spsignup(): 
    if request.method == 'POST':
        user = request.form.get('user_name')
        pwd = request.form.get('password')
        experience = request.form.get('experience')
        service_id = request.form.get('service') # This assumes a dropdown for selecting a service
        full_name = request.form.get('full_name')
        address = request.form.get('location')
        pin = request.form.get('pin_code')

        # Check if the username already exists
        if ServiceProfessional.query.filter_by(username=user).first():
            print('Username already exists!', 'error')
            return render_template('spsignup.html',msg="Sorry, this mail already registered!!!")


        # Create ServiceProfessional with user_id and service_id       
        new_professional = ServiceProfessional(
            username=user, 
            password=pwd, 
            role='professional',
            name=full_name,
            experience=int(experience),
            address=address,
            pincode=int(pin),
            service_id=int(service_id),
        )
        db.session.add(new_professional)
        db.session.commit()
    

        print('Service professional account created successfully!', 'success')
        return redirect(url_for('splogin'))
   
    return render_template("spsignup.html")

@app.route("/splogin", methods=['GET','POST'])
def splogin():
    if request.method == 'POST':
        user = request.form.get('user_name')
        pwd = request.form.get('password')
        user = ServiceProfessional.query.filter_by(username=user, password=pwd).first()
        if user and user.role == 'professional':
            return redirect(url_for('spdashboard'))
        print('Invalid credentials!')
    return render_template("splogin.html")

@app.route("/spdashboard")
def spdashboard():
    return render_template("spdashboard.html")