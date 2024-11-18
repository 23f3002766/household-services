#App routes
from flask import render_template
from flask import current_app as app


@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/spsignup")
def spsignup():
    return render_template("spsignup.html")

@app.route("/login")
def login():
    return render_template("login.html")

#Admin Routes
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

#Customer Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/booking")
def booking():
    return render_template("booking.html")

#Service Personal Routes
@app.route("/spdashboard")
def spdashboard():
    return render_template("spdashboard.html")