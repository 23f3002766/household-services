#App routes
from flask import render_template,redirect,request,url_for
from app import app
from .models import db,User,ServiceProfessional,Customer,Service

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
    services = get_services()
    professionals = get_professionals()
    return render_template("admin_dashboard.html",services=services,professionals=professionals)

@app.route("/admin/createservice", methods=['GET','POST'])
def admin_create_service():
    if request.method == 'POST':
        name = request.form.get('service_name')
        price = request.form.get('price')
        time_required = request.form.get('time_required')
        description = request.form.get('description')
        service = Service.query.filter_by(name=name).first()
        print(service)
        if service:
            print('Service already exists!')
            return redirect(url_for('admin_create_service',msg = 'Service already exists!'))   
        service = Service(name = name,
                          price = float(price),
                          time_required = time_required,
                          description = description
                          )
        print(service)
        db.session.add(service)  
        db.session.commit() 
        return redirect(url_for("admin_dashboard"))     
    return render_template("admin_create_service.html")

@app.route("/admin/editservice/<id>", methods=['GET','POST'])
def admin_edit_service(id):
    service = get_service(id)
    if request.method == 'POST':
        name = request.form.get('service_name')
        price = request.form.get('price')
        time_required = request.form.get('time_required')
        description = request.form.get('description')
        
        if name:
            service.name = name
        if price:
            price = price.split(' ')
            price = price[-1]
            service.price = float(price)
        if time_required:
            service.time_required = time_required
        if description:    
            service.description = description
        
        service.verified = True
        db.session.commit()
        return redirect(url_for("admin_dashboard")) 

         
    return render_template("admin_edit_service.html",service=service)

@app.route("/admin/deleteservice/<id>", methods=['GET','POST'])
def admin_delete_service(id):
    delete_service(id)
    return redirect(url_for("admin_dashboard"))


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
    services = get_services()
    return render_template("dashboard.html",name=name,id=id,services=services)

@app.route("/editprofile/<id>", methods=['GET','POST'])
def edit_profile(id):
    customer = get_customer(id)
    if request.method == 'POST':
        name = request.form.get('user_name')
        pwd = request.form.get('password')
        full_name = request.form.get('full_name')
        location = request.form.get('location')
        pin_code = request.form.get('pin_code')
       
        if name:
            customer.username = name
        if pwd:
            customer.password = pwd
        if full_name:
            customer.name = full_name
        if location:
            customer.address = location
        if pin_code:
            customer.pincode = int(pin_code)
        customer.verified = True  
        db.session.commit()
        return redirect(url_for("dashboard",name = customer.name,id=customer.id)) 

         
    return render_template("edit_profile.html",user=customer)

@app.route("/deleteuser/<id>", methods=['GET','POST'])
def delete_profile(id):
    delete_customer(id)
    return redirect(url_for("login"))

@app.route("/booking/<id>")
def booking(id):
    professionals = ServiceProfessional.query.filter_by(service_id=id).all()
    print(professionals)
    return render_template("booking.html",id=id,professionals=professionals)

#Service Personal Routes
@app.route("/spsignup", methods = ['GET','POST'])
def spsignup(): 
    
    if request.method == 'POST':
        user = request.form.get('user_name')
        pwd = request.form.get('password')
        experience = request.form.get('experience')
        service = request.form.get('service') # This assumes a dropdown for selecting a service
        full_name = request.form.get('full_name')
        address = request.form.get('location')
        phone = request.form.get('phone')
        pin = request.form.get('pin_code')
        service = service.split('|')
        print(service[0])
        # Check if the username already exists
        if ServiceProfessional.query.filter_by(username=user).first():
            print('Username already exists!', 'error')
            return render_template('spsignup.html',msg="Sorry, this mail already registered!!!")

        service_id = service[0].strip()
        service_type = service[1].strip()
        # Create ServiceProfessional with user_id and service_id       
        new_professional = ServiceProfessional(
            username= user, 
            password= pwd, 
            role='professional',
            name=full_name,
            experience=int(experience),
            address=address,
            phone=int(phone),
            pincode=int(pin),
            service_id= int(service_id),
            service_type= service_type
        )
        db.session.add(new_professional)
        try:
            db.session.commit()
            print('Service professional account created successfully!', 'success')
            return redirect(url_for('splogin'))
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
        finally:
            db.session.close()
            db.session.commit()

        return redirect(url_for('spsignup'))
    

        
    services = get_services()
    return render_template("spsignup.html",services=services)

@app.route("/splogin", methods=['GET','POST'])
def splogin():
    if request.method == 'POST':
        user = request.form.get('user_name')
        pwd = request.form.get('password')
        user = ServiceProfessional.query.filter_by(username=user, password=pwd).first()
        if user and user.role == 'professional':
            return redirect(url_for('spdashboard',id = user.id))
        print('Invalid credentials!')
    return render_template("splogin.html")

@app.route("/spdashboard/<id>")
def spdashboard(id):
    return render_template("spdashboard.html",id=id)

@app.route("/editprofessional/<id>", methods=['GET','POST'])
def edit_professional(id):
    professional = get_professional(id)
    if request.method == 'POST':
        name = request.form.get('user_name')
        pwd = request.form.get('password')
        full_name = request.form.get('full_name')
        experience = request.form.get('experience')
        address = request.form.get('location')
        pin_code = request.form.get('pin_code')
        phone = request.form.get('phone')
       
        if name:
            professional.username = name
        if pwd:
            professional.password = pwd
        if full_name:
            professional.name = full_name
        if experience:
            professional.experience = int(experience)
        if address:
            professional.address = address
        if pin_code:
            professional.pincode = int(pin_code)
        if phone:
            professional.phone = int(phone)

        professional.verified = True  
        db.session.commit()
        return redirect(url_for("spdashboard",id=professional.id)) 

    return render_template("edit_professional.html",user=professional)


@app.route("/deleteprofessional/<id>", methods=['GET','POST'])
def delete_professional(id):
    delete_professional(id)
    return redirect(url_for("splogin"))

#Admin Helper Functions
def get_services():
    services = Service.query.all()
    return services

def get_service(id):
    service = Service.query.filter_by(id=id).first()
    return service
def delete_service(id):
    service = get_service(id)
    db.session.delete(service)
    db.session.commit()
    return

#service Professional Helper Functions
def get_professionals():
    professionals = ServiceProfessional.query.all()
    return professionals

def get_professional(id):
    user = ServiceProfessional.query.filter_by(id=id).first()
    return user

def delete_professional(id):
    user = get_professional(id)
    db.session.delete(user)
    db.session.commit()
    return

#Customer helper Functions
def get_customer(id):
    user = Customer.query.filter_by(id=id).first()
    return user

def delete_customer(id):
    user = get_customer(id)
    db.session.delete(user)
    db.session.commit()
    return