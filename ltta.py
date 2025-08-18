from flask import *
from flask_login import *
from utils.logger import Logger
from flask_session import Session
import flask_login

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
import glob

## others

# imports

app = Flask(__name__)
app.secret_key = "dummy_key"
app.template_folder = "templates/"
app.static_folder = "static/"

# app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_COOKIE_HTTPONLY'] = False # While PROD replace on True
# app.config['SESSION_COOKIE_SECURE'] = False # While PROD replace on True
# app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 


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

            

        logger.log("info", f"New registration detected: {username} {email} {name} {surname} {password} {repeat_password} {grade} {faculty}")
        
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(message_html.replace("VERIFICATION_CODE", f"{code}"), "html", "utf-8"))
        message["from"] = "glebocrew@yandex.ru"

        try:
            global server
            server.sendmail(sender_email, email, message.as_string())
            logger.log("info", f"Sending verification code to {email}.")

            connection.insert_new_temp_profile("codes", username, code, datetime.now(), email, name, surname, grade, faculty, password)
        except smtplib.SMTPSenderRefused or smtplib.SMTPRecipientsRefused as e:
            logger.log("error", f"Sending code on {email} failed because of its incorrectance! Full error {e}.")
            return render_template("registration.html", message="Invalid email!")

        except smtplib.SMTPServerDisconnected as e:
            logger.log("error", f"SMTP server was disconnected! Trying to reconnect! Full error {e}")

            try:
                server = smtplib.SMTP_SSL(smtp_server, port, context=context)
                server.login(sender_email, password)
            except Exception as e:
                logger.log("fatal", f"SMTP server was disconnected! Full error {e}")
                
            return render_template("registration.html", message="Invalid email!")



        # TODO: email 
        return redirect(url_for("verification", email=email))

    return render_template("registration.html")

@app.route("/verification/<email>", methods = ['GET', 'POST'])
def verification(email):
    if request.method == 'POST': # TODO: actions after verification (insertation in table users)
        temp_user = connection.get_temp_profile_by_email("codes", email)   
        code_time = datetime.strptime(temp_user[2], "%Y-%m-%d %H:%M:%S.%f")


        if (datetime.now() - code_time).total_seconds() > 300: # in secs (300)
            flash("Code timeout. Try again!")
            return redirect("/registration")
        

        if str(request.form.get("code")) == temp_user[1]:
            # TODO: create a new user in MAIN users table
            connection.create_new_user("users", temp_user[7], temp_user[3], temp_user[4], temp_user[0], temp_user[8], temp_user[5], temp_user[6])
            connection.drop_temp_profile_by_email("codes", email)
            return redirect("/login")
        else:
            return redirect(url_for('verification', email=email))

    return render_template('verification.html', email=email)

@app.route("/profile")
@login_required
def profile():
    logger.log("info", f"{current_user.id}")
    user_data = connection.get_user_by_username("users", current_user.id)
    if user_data != -1:
        return render_template("profile.html", user_data=user_data)
    
@app.route("/change_profile", methods = ['GET', 'POST'])
@login_required
def change_profile():
    user_data = connection.get_user_by_username("users", current_user.id)
    if user_data != -1:
        if request.method == "POST":
            avatar = request.files.get("avatar")
            extention = avatar.filename[-3:]
            logger.log("info", f"avatar: {avatar}")

            if avatar and avatar.filename != "":
                if user_data["avatar"].split(sep="/")[-1] != "default.png":
                    logger.log("info", f"Updating avatar for {user_data['username']}.")

                    to_delete = glob.glob(f"static/img/avatars/{user_data['username']}.*")
                    logger.log("info", f"Deleting previous avatars aka {to_delete}.")
                    
                    if to_delete:
                        for file in to_delete:    
                            os.remove(file)
                            logger.log("info", f"Deleting {file}")
                try:
                    logger.log("info", f"Creating file {user_data['username']}.{extention}")

                    avatar.save(f"static/img/avatars/{user_data['username']}.{extention}")
                    # avatar_bits = open(avatar, "rb").read()
                    # new_avatar = open(f"{user_data['username']}.{avatar.filename[-3:]}", "wr")

                    user_data["avatar"] = f"img/avatars/{user_data['username']}.{extention}"

                    # new_avatar.write(avatar_bits)


                    logger.log("info", "File successfully created")
                except Exception as e:
                    logger.log("error", f"File was not created! Full error: {e}")


                # TODO: creating new avatar and inserting path to mariadb

            username = request.form.get("username")

            if connection.find_user_by_username("users", username) and username != user_data["username"]:
                return render_template("change_profile.html", user_data=user_data, message="This username is already taken!")
 

            if username != user_data["username"]:
                if user_data["avatar"].split("/")[-1] != "default.png":
                    user_avatars = glob.glob(f"static/img/avatars/{user_data['username']}.*")
                    try:
                        logger.log("info", f"Renaming files caused by username change.")
                        for user_avatar in user_avatars:
                            logger.log("info", f"extention: {user_data["avatar"][-3:]}")
                            os.rename(user_avatar, f"static/img/avatars/{username}.{user_data["avatar"][-3:]}")
                        user_data["avatar"] = f"img/avatars/{username}.{user_data["avatar"][-3:]}"
                        logout_user()


                    except Exception as e:
                        logger.log("error", f"Renaming failed! Full error {e}")

            
            name = request.form.get("name")
            surname = request.form.get("surname")
            # password = request.form.get("password")         
            grade = request.form.get("grade")
            faculty = request.form.get("faculty")
            email = request.form.get("email") # """UPDATE table_name SET username = ?, name = ?, surname = ?, email = ?, grade = ?, faculty = ?, avatar = ? WHERE username = ?;"""

            
            connection.update_profile("users", username, name, surname, email, grade, faculty, user_data["avatar"], user_data["username"])
            return redirect("/profile")

        return render_template("change_profile.html", user_data=user_data)

@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")



# routes

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large")
    return redirect("/change_profile")

# errors

if __name__ == "__main__":
    app.run(host='0.0.0.0')
    logger.stop()

# start point

