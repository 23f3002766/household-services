#Starting of the app
from flask import Flask



app = None

def setup_app():
    global app
    app=Flask(__name__)
    app.app_context().push() #Direct access to other modules
    print("HouseHold Services App is started...")
    
#Initializing server
setup_app()

from backend.controllers import *

if __name__=="__main__": 
    app.run(debug = True)