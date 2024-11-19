#Starting of the app
from flask import Flask
from backend.models import db



app = None

def setup_app():
    global app
    app=Flask(__name__)
    app.app_context().push() #Direct access to other modules
    app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///services_app.sqlite3"
    db.init_app(app)
    print("HouseHold Services App is started...")
    
#Initializing server
setup_app()

from backend.controllers import *

if __name__=="__main__": 
    app.run(debug = True)