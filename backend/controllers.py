#App routes
from flask import render_template,redirect,request,url_for,send_from_directory
from app import app
from .models import db,User,ServiceProfessional,Customer,Service,ServiceRequest
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
import io
import base64
import matplotlib

matplotlib.use('Agg') 

UPLOAD_FOLDER = 'uploads/professional_pdfs'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    serv_reqs = get_service_reqs()
    customers = get_customers()
    #formating for frontend
    for req in serv_reqs:
        req.date_of_request = str(req.date_of_request).split(' ')[0]

        # Get the professional name using the professional_id in ServiceRequest
        if req.professional_id:
            professional = ServiceProfessional.query.get(req.professional_id)
            req.professional_name = professional.name if professional else "Unassigned"
        else:
            req.professional_name = "Unassigned"
        
    return render_template("admin_dashboard.html",serv_reqs=serv_reqs,services=services,professionals=professionals,customers=customers)

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

@app.route("/admin/deleteuser/<id>", methods=['GET','POST'])
def admin_delete_user(id):
    delete_customer(id)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/profaprov/<id>")
def prof_aprov(id):
    prof = get_professional(id)
    prof.approved = True
    prof.blocked = False
    prof.verified = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/rejaprov/<id>")
def prof_rej(id):
    prof = get_professional(id)
    reqs = get_service_requests_for_prof(id)
    for req,user in reqs:
        delete_req(req.id)

    if prof.approved:
        prof.approved = False
    prof.blocked = True
    prof.verified = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route('/admin/viewpdf/<professional_id>')
def view_pdf(professional_id):
    professional = ServiceProfessional.query.filter_by(id=professional_id).first()
    if professional and professional.pdf_path:
        directory = os.path.dirname(professional.pdf_path)  # Extract the folder path
        filename = os.path.basename(professional.pdf_path)  # Extract the file name
        try:
            return send_from_directory(
                directory=directory,
                path=filename,
                as_attachment=False  # Set to True if you want the browser to download the file
            )
        except FileNotFoundError:
            return "File not found!", 404
    return "Professional or document not found!", 404

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
            services = get_services()
            reqs = get_service_requests_for_user(user.id)
            return redirect(url_for('dashboard',name=user.name,id=user.id,services=services,reqs=reqs))
        print('Invalid credentials!')
    return render_template("login.html")

@app.route("/dashboard/<id>/<name>")
def dashboard(id,name):
    services = get_services()
    reqs = get_service_requests_for_user(id)
    for req in reqs:
        req.date_of_request = str(req.date_of_request).split(' ')
        req.date_of_request = req.date_of_request[0].strip()

        if req.date_of_completion:
            req.date_of_completion = str(req.date_of_completion).split(' ')
            req.date_of_completion = req.date_of_completion[0].strip()
        else:
            req.date_of_completion = 'DND'
    return render_template("dashboard.html",name=name,id=id,services=services,reqs=reqs)

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
        services = get_services()
        reqs = get_service_requests_for_user(id)
        return redirect(url_for("dashboard",name = customer.name,id=customer.id,services=services,reqs=reqs)) 

         
    return render_template("edit_profile.html",user=customer)

@app.route("/editreq/<uid>/<id>", methods=['GET','POST'])
def edit_req(uid,id):

    services = get_services()
    customer = get_customer(uid)
    reqs = get_service_requests_for_user(uid)

    if request.method == 'POST':
        date = request.form.get('date')
        
        if date:
            formatted_date = datetime.strptime(date.strip("[]"), "%Y-%m-%dT%H:%M")
            req = get_req(id)
            req.date_of_request = formatted_date
            req.verified = True
            db.session.commit()
            print("date changed successfully!!!")
            return redirect(url_for("dashboard",name = customer.name,id=customer.id,services=services,reqs=reqs))
            
    return redirect(url_for("dashboard",name = customer.name,id=customer.id,services=services,reqs=reqs))


@app.route("/addremark/<uid>/<name>/<id>", methods=['GET','POST'])
def add_remark(uid,name,id):

    services = get_services()
    customer = get_customer(uid)
    reqs = get_service_requests_for_user(uid)

    if request.method == 'POST':
        remark = request.form.get('remark')
        
        if remark:
            req = get_req(id)
            req.remarks = remark
            req.verified = True
            db.session.commit()
            print("Rating added successfully!!!")
            return redirect(url_for("dashboard",name = name,id=customer.id,services=services,reqs=reqs))
            
    return redirect(url_for("dashboard",name = customer.name,id=customer.id,services=services,reqs=reqs))

@app.route("/deleteuser/<id>", methods=['GET','POST'])
def delete_profile(id):
    delete_customer(id)
    return redirect(url_for("login"))

@app.route("/booking/<name>/<uid>/<sid>")
def booking(name,uid,sid):
    professionals = ServiceProfessional.query.filter_by(service_id=sid).all()
    print(professionals)
    return render_template("booking.html",name=name,uid=uid,sid=sid,professionals=professionals)

@app.route("/closereq/<uid>/<name>/<id>")
def close_req(uid,name,id):
    req = get_req(id)
    if req.service_status == 'assigned':
        req.service_status = 'closed'
        req.date_of_completion = datetime.now()
        req.verified = True
        db.session.commit()
        print('req closed!!')
        if req.date_of_completion:
            req.date_of_completion = str(req.date_of_completion).split(' ')
            req.date_of_completion = req.date_of_completion[0]

        return redirect(url_for("dashboard",id=uid,name=name))
    print('req did not close!!')
    return redirect(url_for("dashboard",id=uid,name=name))

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
        # Check if the username already exists
        if ServiceProfessional.query.filter_by(username=user).first():
            print('Username already exists!', 'error')
            return render_template('spsignup.html',msg="Sorry, this mail already registered!!!")

        service_id = service[0].strip()
        service_type = service[1].strip()
        #saving file path
        pdf = request.files.get('vdoc')
        print("Uploaded file:",pdf)
        if pdf and allowed_file(pdf.filename):
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            filename = secure_filename(pdf.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf.save(pdf_path)
        else:
            print("Please upload a valid PDF.", "error")
            return redirect(url_for('spsignup'))
        
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
            service_type= service_type,
            pdf_path=pdf_path
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
            return redirect(url_for('spdashboard',id = user.id,prof=user))
        print('Invalid credentials!')
    return render_template("splogin.html")

@app.route("/spdashboard/<id>")
def spdashboard(id):

    serv_reqs = get_service_requests_for_prof(id)
    prof = get_professional(id)
    for req,user in serv_reqs:
        print(req,user)
        req.customer = get_customer(req.customer_id)
        req.service = get_service(req.service_id)
        print(req.customer,req.service)
    
    for req,user in serv_reqs:
        if req.date_of_completion:
            req.date_of_completion = str(req.date_of_completion).split(' ')
            req.date_of_completion = req.date_of_completion[0]

    return render_template("spdashboard.html",id=id,reqs=serv_reqs,prof = prof)

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
        return redirect(url_for("spdashboard",id=professional.id,prof=professional)) 

    return render_template("edit_professional.html",user=professional)


@app.route("/deleteprofessional/<id>", methods=['GET','POST'])
def delete_professional(id):
    delete_professional(id)
    return redirect(url_for("splogin"))

@app.route("/acceptreq/<pid>/<sid>")
def req_aprov(pid,sid):
    req = get_req(sid)
    prof = get_professional(pid)
    if req.service_status == 'requested':
        req.service_status = 'assigned'
        req.verified = True
        db.session.commit()
        print('assigned sucessfully!!!')
        return redirect(url_for("spdashboard",id=pid,prof = prof))
    if req.service_status == 'closed':
        print('Req Closed!!')
        return redirect(url_for("spdashboard",id=pid,prof = prof))
    print('Already assigned')
    return redirect(url_for("spdashboard",id=pid,prof = prof))


#Service Request Routes
@app.route('/servicereq/create/<name>/<uid>/<pid>/<sid>', methods = ['GET','POST'])
def create_service_req(name,uid,pid,sid):

    date = request.form.get('date')   
    
    reqs = get_service_requests_for_user(uid)
    for req in reqs:
        if str(req.service_status)  in ["assigned", "requested"]:  
            if str(req.professional_id) == str(pid):
                print(req.professional_id,pid)
                print("hi From")
                print("Request already underway by the professional")
                return redirect(url_for('booking',name=name,uid=uid,sid=sid))
        

    if date:
        formatted_date = datetime.strptime(date.strip("[]"), "%Y-%m-%dT%H:%M")
        service_req = ServiceRequest(
        service_id = int(sid),
        customer_id = int(uid),
        professional_id = int(pid),
        date_of_request = formatted_date  
    )
    else :
        service_req = ServiceRequest(
        service_id = int(sid),
        customer_id = int(uid),
        professional_id = int(pid) 
    )
    db.session.add(service_req)
    db.session.commit()
    print('Booking successfull')
    return redirect(url_for('booking',name=name,uid=uid,sid=sid))

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
def delete_user(id):
    user = get_customer(id)
    db.session.delete(user)
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

def get_customers():
    customers = Customer.query.all()
    return customers

def delete_customer(id):
    user = get_customer(id)
    db.session.delete(user)
    db.session.commit()
    return

def get_service_requests_for_user(uid):
    serv_reqs = (
        db.session.query(ServiceRequest)
        .join(Customer, ServiceRequest.customer_id == Customer.id)
        .filter(Customer.id == uid)
        .all()
    )
    for req in serv_reqs:
        print(req)
        req.prof = get_professional(req.professional_id)
        req.service = get_service(req.service_id)
        print(req.prof,req.service)
    return serv_reqs

#Service request Helper Functions
def get_service_reqs():
    service_reqs = ServiceRequest.query.all()
    return service_reqs

def get_req(id):
    req = ServiceRequest.query.filter_by(id=id).first()
    return req

def get_service_requests_for_prof(pid):
    serv_reqs = (
        db.session.query(ServiceRequest , ServiceProfessional.username)
        .join(ServiceProfessional, ServiceRequest.professional_id == ServiceProfessional.id)
        .filter(ServiceProfessional.id == pid)
        .all()
    )
    return serv_reqs

def delete_req(id):
    req = get_req(id)
    db.session.delete(req)
    db.session.commit()
    return

#Search functionality
@app.route("/search/<id>/<name>",methods=["GET","POST"])
def search(id,name):
    if request.method=="POST":
        search_txt=request.form.get("search_txt")
        opt = request.form.get('filter_category')
        

        if str(opt) == 'Address':
            by_add=search_by_address(search_txt)
            print(by_add)
            return render_template("search.html",results=by_add,id=id,name=name)
        elif str(opt) == 'Service':       
            by_type=search_by_service_type(search_txt)
            print(by_type) 
            return render_template("search.html",results=by_type,id=id,name=name)

    return render_template("search.html",id=id,name=name)

@app.route("/admin/search",methods=["GET","POST"])
def admin_search():
    if request.method=="POST":
        search_txt=request.form.get("search_txt")
        opt = request.form.get('filter_category')  

        if str(opt) == 'Address':
            by_add=search_by_address(search_txt)
            print(by_add)
            return render_template("admin_search.html",results=by_add)
        elif str(opt) == 'Service':       
            by_type=search_by_service_type(search_txt)
            print(by_type) 
            return render_template("admin_search.html",results=by_type)

    return render_template("admin_search.html")

def search_by_address(search_txt):
    profs=ServiceProfessional.query.filter(ServiceProfessional.name.ilike(f"%{search_txt}%")).all()
    return profs

def search_by_service_type(search_txt):
   profs=ServiceProfessional.query.filter(ServiceProfessional.service_type.ilike(f"%{search_txt}%")).all()
   return profs


#Chart Routes
@app.route('/admin/summary')
def admin_summary():
    # Data aggregation
    service_counts = db.session.query(Service.name, db.func.count(ServiceRequest.id))\
        .join(ServiceRequest, Service.id == ServiceRequest.service_id)\
        .group_by(Service.name).all()
    
    services = [row[0] for row in service_counts]
    counts = [row[1] for row in service_counts]

    # Generate Matplotlib chart
    plt.figure(figsize=(6, 4))
    plt.bar(services, counts, color='skyblue')
    plt.xlabel('Services')
    plt.ylabel('Number of Requests')
    plt.title('Service Requests per Service')
    plt.xticks(rotation=45)

    # Convert plot to a base64 string to embed in HTML
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    img.close()

    return render_template(
        'admin_summary.html',
        chart_url=f"data:image/png;base64,{chart_url}",
        total_professionals=ServiceProfessional.query.count(),
        total_customers=Customer.query.count(),
        total_requests=ServiceRequest.query.count()
    )

#Professionals chart
@app.route('/professional/summary/<int:professional_id>')
def professional_summary(professional_id):
    # Get the professional's details
    professional = ServiceProfessional.query.get(professional_id)

    # Fetch service requests handled by this professional
    service_requests = ServiceRequest.query.filter_by(professional_id=professional_id).all()

    # Count requests by status
    status_counts = db.session.query(
        ServiceRequest.service_status, db.func.count(ServiceRequest.id)
    ).filter_by(professional_id=professional_id).group_by(ServiceRequest.service_status).all()

    statuses = [row[0] for row in status_counts]
    counts = [row[1] for row in status_counts]

    # Generate chart for service statuses
    plt.figure(figsize=(6, 4))
    plt.pie(counts, labels=statuses, autopct='%1.1f%%', startangle=140, colors=['lightblue', 'lightgreen', 'salmon'])
    plt.title('Service Request Status Distribution')

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    img.close()

    return render_template(
        'professional_summary.html',
        professional=professional,
        chart_url=f"data:image/png;base64,{chart_url}",
        total_requests=len(service_requests),
        assigned_requests=len([req for req in service_requests if req.service_status == 'assigned']),
        completed_requests=len([req for req in service_requests if req.service_status == 'closed'])
    )

#Customer Chart
@app.route('/customer/summary/<int:customer_id>/<name>')
def customer_summary(customer_id,name):
    # Get the customer's details
    customer = Customer.query.get(customer_id)

    # Fetch service requests made by this customer
    service_requests = ServiceRequest.query.filter_by(customer_id=customer_id).all()

    # Count requests by service
    service_counts = db.session.query(
        Service.name, db.func.count(ServiceRequest.id)
    ).join(Service, Service.id == ServiceRequest.service_id)\
     .filter(ServiceRequest.customer_id == customer_id)\
     .group_by(Service.name).all()

    services = [row[0] for row in service_counts]
    counts = [row[1] for row in service_counts]

    # Generate chart for services requested
    plt.figure(figsize=(6, 4))
    plt.bar(services, counts, color='skyblue')
    plt.xlabel('Services')
    plt.ylabel('Number of Requests')
    plt.title('Services Requested by Customer')
    plt.xticks(rotation=45)

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    img.close()

    return render_template(
        'customer_summary.html',
        customer=customer,
        chart_url=f"data:image/png;base64,{chart_url}",
        total_requests=len(service_requests),
        pending_requests=len([req for req in service_requests if req.service_status == 'requested']),
        completed_requests=len([req for req in service_requests if req.service_status == 'closed']),
        name=name,
        id=customer_id
    )

