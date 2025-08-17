from flask import *
from flask_login import *
from utils.logger import Logger
from flask_session import Session

## flask

from db_ops import MariaConnection, User
import sys, os
import db_ops

## db

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

## email

from hashlib import sha256
from json import load
from random import randint
from datetime import datetime, timedelta
import secrets

## others

# imports

app = Flask(__name__)
app.secret_key = "dummy_key"
app.template_folder = "templates/"
app.static_folder = "static/"

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 

Session(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# flask app conf

logger = Logger("logs/logs.txt", __file__)

# logger conf

try:
    logger.log("info", f"[{os.getpid()}] Loading email configure.")
    json_conf = load(open("conf.json"))

    port = json_conf["mailbox"]["port"]
    smtp_server = json_conf["mailbox"]["smtp_server"]
    sender_email = json_conf["mailbox"]["sender_email"]
    password = json_conf["mailbox"]["password"]
    message_html = open("templates/email/email.html", "r", encoding="utf-8").read()

    context = ssl.create_default_context()

    server = smtplib.SMTP_SSL(smtp_server, port, context=context)

    server.login(sender_email, password)

    # logger.log("info", f"{connection}")
    logger.log("info", f"[{os.getpid()}] Successfully loaded mailbox conofs.")
except Exception as e:
    logger.log("error", f"[{os.getpid()}] There are no mailbox configure file (or the syntax is incorrect).")
    logger.log("fatal", f"[{os.getpid()}] The main app was stopped since there're no mailbox confs. Fill exception: {e}")
    sys.exit(1)




# email conf

try:
    logger.log("info", f"[{os.getpid()}] Loading mariadb configure.")
    json_conf = load(open("conf.json"))
    connection = MariaConnection(json_conf["db"])
    # logger.log("info", f"{connection}")
    logger.log("info", f"[{os.getpid()}] Successfully loaded mariadb confs.")
except:
    logger.log("error", f"[{os.getpid()}] There are no database configure file.")
    logger.log("fatal", f"[{os.getpid()}] The main app was stopped since there're no mariadb confs.")
    sys.exit(1)

# mariadb conf

@login_manager.user_loader
def load_user(username):
    return User(username)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        ## TODO: mariadb check in database V COMPLTED
        username = request.form.get("username")
        # username 

        password = sha256()
        password.update(request.form.get("password").encode("utf-8"))
        password = password.hexdigest()
        # hashed password

        if connection.find_user_by_login_and_password("users", username, password):
            user = User(username)
            login_user(user)
            logger.log("info", f"new SUCCESFULL login: username={username} password={password}")

            return redirect(url_for("index"))
        else:
            return render_template("login.html", message="go to /registration to register a new account") ## TODO: it's only if args are incorrect V COMPLETED
        
    return render_template("login.html")

@app.route("/registration", methods = ['GET', 'POST'])
def registration():
    if request.method == 'POST':
        if "last_submit" in session:
            if datetime.now() - session["last_submit"] < timedelta(minutes=1): 
                remaining = (timedelta(minutes=1) - (datetime.now() - session["last_submit"])).seconds
                return render_template("registration.html", message=f"The form hasn't been sent! Please wait {remaining} seconds")

        username = request.form.get("username") # TODO: if username is not in mariadb! V COMPLETED

        if connection.find_user_by_username("users", username):
            return render_template("registration.html", message="This username is already taken!")
            
        password = sha256()
        password.update(request.form.get("password").encode("utf-8"))
        
        repeat_password = sha256()
        repeat_password.update(request.form.get("repeat_password").encode("utf-8"))

        password = password.hexdigest() 
        repeat_password = repeat_password.hexdigest() # TODO: if passwords match! V COMPLETED

        name = request.form.get("name")
        surname = request.form.get("surname")        

        if password != repeat_password:
            return render_template("registration.html", message="The passwords don't match!")

        email = request.form.get("email") # TODO: if email is not in mariadb V COMPLETED

        if connection.find_user_by_email("users", email):
            return render_template("registration.html", message="This email is already used!")

        grade = request.form.get("grade")

        faculty = request.form.get("faculty")

        code = ''.join(secrets.choice('0123456789qwertyuiopasdfghjklzxcvbnm') for _ in range(6))
        
        session["temp_user"] = {
                "username": username,
                "password": password,
                "name": name,
                "surname": surname,
                "email": email,
                "grade": grade,
                "faculty": faculty,
                "code": code
        }
            

        logger.log("info", f"New registration detected: {username} {email} {name} {surname} {password} {repeat_password} {grade} {faculty}")
        
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(message_html.replace("VERIFICATION_CODE", f"{code}"), "html", "utf-8"))
        message["from"] = "glebocrew@yandex.ru"

        server.sendmail(sender_email, email, message.as_string())

        session['last_submit'] = datetime.now()
        session.modified = True


        # TODO: email 
        return redirect(url_for("verification", email=email))

    return render_template("registration.html")

@app.route("/verification/<email>", methods = ['GET', 'POST'])
def verification(email):
    if request.method == 'POST': # TODO: actions after verification (insertation in table users)
        logger.log("INFO", f"Entered a code with: {session}")
        if "temp_user" not in session or "code" not in session['temp_user']:
            return redirect("/login") # replace to /registration after test
        
        if request.form.get("code") == session["temp_user"]["code"]:
            return redirect("/login")
        else:
            return redirect(url_for('verification', email=email))

    return render_template('verification.html', email=email)

@app.route("/profile")
@login_required
def profile():
    return "<h1>profile</h1>"
# routes

if __name__ == "__main__":
    app.run(host='0.0.0.0')
    logger.stop()

# start point

