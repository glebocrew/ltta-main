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
from functools import wraps

import secrets
import glob
import pytz

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
    return User(username, connection.get_user_role_by_username("users", username))



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
            user = User(username, connection.get_user_role_by_username("users", username))
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
        
        try:
            logger.log("info", f"[{os.getpid()}] Loading email configure.")
            json_conf = load(open("conf.json"))

            port = json_conf["mailbox"]["port"]
            smtp_server = json_conf["mailbox"]["smtp_server"]
            sender_email = json_conf["mailbox"]["sender_email"]
            password_smtp = json_conf["mailbox"]["password"]
            message_html = open("templates/email/email.html", "r", encoding="utf-8").read()

            context = ssl._create_unverified_context()

            server = smtplib.SMTP_SSL(smtp_server, port, context=context)

            server.login(sender_email, password_smtp)

            # logger.log("info", f"{connection}")
            logger.log("info", f"[{os.getpid()}] Successfully loaded mailbox conofs.")
        except Exception as e:
            logger.log("error", f"[{os.getpid()}] There are no mailbox configure file (or the syntax is incorrect).")
            logger.log("fatal", f"[{os.getpid()}] The main app was stopped since there're no mailbox confs. Fill exception: {e}")
            sys.exit(1)


        message = MIMEMultipart("alternative")
        message.attach(MIMEText(message_html.replace("VERIFICATION_CODE", f"{code}"), "html", "utf-8"))
        message["From"] = "LTTA TEAM <ltta@glebocrew.ru>"
        message['Subject'] = 'Your Verification Code'
        message["To"] = f"{name} {surname} <{email}>"

        try:
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

        server.quit()
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
    
@app.route("/edit_profile", methods = ['GET', 'POST'])
@login_required
def edit_profile():
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
                return render_template("edit_profile.html", user_data=user_data, message="This username is already taken!")
 

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

        return render_template("edit_profile.html", user_data=user_data)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/members", methods=['GET', 'POST'])
@login_required
def members():
    logger.log("info", f"Trying to get in admin page: {current_user.id, current_user.role}")
    if 'admin' in current_user.role:
        members = connection.get_all_users("users")

        if request.method == 'POST':
            logger.log("info", f"Building url for {request.form.get('username')}")
            return redirect(url_for("member", user=request.form.get("username")))

        return render_template("admin/members.html", members=members)
    else:
        return redirect("/")

@app.route("/member/<user>")    
@login_required
def member(user):
    user_data = connection.get_user_by_username("users", user)
    return render_template("admin/profile_admin_view.html", user_data=user_data)

@app.route("/member/<user>/edit_profile", methods=['GET', 'POST'])
def edit_profile_admin(user):
    user_data = connection.get_user_by_username("users", user)
    admin_name_surname = connection.get_user_name_surname("users", current_user.id)
    
    if request.method == 'POST':
        avatar = request.files.get("avatar")

        extention = avatar.filename[-3:]

        logger.log("info", f"avatar: {avatar}")

        if "admin" not in user_data["role"]:

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
                return render_template("admin/edit_profile_admin_view.html", user_data=user_data, admin_name_surname=admin_name_surname, message="This username is already taken!")

            if username != user_data["username"]:
                if user_data["avatar"].split("/")[-1] != "default.png":
                    user_avatars = glob.glob(f"static/img/avatars/{user_data['username']}.*")
                    try:
                        logger.log("info", f"Renaming files caused by username change.")
                        for user_avatar in user_avatars:
                            logger.log("info", f"extention: {user_data["avatar"][-3:]}")
                            os.rename(user_avatar, f"static/img/avatars/{username}.{user_data["avatar"][-3:]}")
                        user_data["avatar"] = f"img/avatars/{username}.{user_data["avatar"][-3:]}"
                    except Exception as e:
                        logger.log("error", f"Renaming failed! Full error {e}")

            name = request.form.get("name")
            surname = request.form.get("surname")
            # password = request.form.get("password")         
            grade = request.form.get("grade")
            faculty = request.form.get("faculty")
            role = request.form.get("role")
            rating = request.form.get("rating")
            email = request.form.get("email") # """UPDATE table_name SET username = ?, name = ?, surname = ?, email = ?, grade = ?, faculty = ?, avatar = ? WHERE username = ?;"""

            connection.admin_update_profile("users", username, name, surname, email, grade, faculty, user_data["avatar"], rating, role, user_data["username"])
            return redirect(url_for("member", user=username))
        else:
            flash("Cannot edit admin!")
            return redirect("/members")

    return render_template("admin/edit_profile_admin_view.html", user_data=user_data, admin_name_surname=admin_name_surname)

@app.route("/events_list", methods=['GET', 'POST'])
@login_required
def events_list():
    if "users" in current_user.role:
        return redirect("/")
    # TODO: list of events display
    events = connection.get_all_events("events")

    # logger.log("debug", f"{events[0]["datetime"]}")

    if request.method == "POST":
        event_title = request.form.get("event_title")
        if request.form.get("action") == "edit":
            return redirect(url_for("edit_event", event=event_title))
            pass
        elif request.form.get("action") == "delete":
            connection.delete_event_by_title("events", event_title)
            
            i = 0
            event_id = 0
            for event in events:
                if event["title"] == event_title:
                    event_id = i
                    break
                i += 1

            # print(f"styles/{events[event_id]['image']}")
            # print(glob.glob(f"styles/{events[event_id]['image']}"))

            path = f"static/{events[event_id]['image']}"
            try:
                logger.log("info", f"Deleting old event image static/{path} ")
                os.remove(path)
            except Exception as e:
                logger.log("error", f"Deleting old event image static/{path} failed! Full error {e}")
            
            return redirect("events_list")

    return render_template("admin_editor/events_list.html", events=events)


@app.route("/create_event", methods=['GET', 'POST'])
@login_required
def create_event():
    if "user" in current_user.role:
        return redirect("/")
    
    if request.method == "POST":

        event_type = request.form.get("type")
        title = request.form.get("title")
        content = request.form.get("content")
        timezone = request.form.get("timezone")

        logger.log("info", f" User timezone is {timezone}")

        datetime_form = request.form.get("datetime")
        datetime_form = datetime.strptime(datetime_form, "%Y-%m-%dT%H:%M")

        # user_timezone = pytz.timezone(timezone)
        # user_datetime = user_timezone.localize(datetime_form)

        # datetime_form = user_datetime.astimezone(pytz.UTC)


        image = request.files.get("image")
        
        status  = os.path.exists(f'static/img/events/{image.filename}')
        logger.log("info", f"File static/img/events/{image.filename} status by os: {status}")
        if os.path.exists(f"static/img/events/{image.filename}"):
            logger.log("info", f"Removing static/img/events/{image.filename}")
            os.remove(f"static/img/events/{image.filename}")
        
        logger.log("info", f"Creating static/img/events/{image.filename}")
        open(f"static/img/events/{image.filename}", "a").close()

        logger.log("info", f"Saving event image to static/img/events/{image.filename}")
        image.save(f"static/img/events/{image.filename}")

        connection.create_event("events", event_type, title, datetime_form, content, f"img/events/{image.filename}")

        return redirect("events_list")

        
    return render_template("admin_editor/create_event.html")


@app.route("/edit_event/<event>", methods=['GET', 'POST'])
@login_required
def edit_event(event):
    if "users" in current_user.role:
        return redirect("/")
    event_info = connection.get_event_by_title("events", event)
    event_info["datetime"] = datetime.strptime(event_info["datetime"], "%Y-%m-%d %H:%M:%S")

    # event_info["datetime"] = datetime.strptime(event_info["datetime"], "%Y-%m-%d %H:%M") + timedelta(hours=3)
    # event_info["datetime"] = datetime.strptime(event_info["datetime"], "%Y-%m-%d %H:%M:%S")

    event_info["datetime"] = event_info["datetime"].strftime("%Y-%m-%dT%H:%M")

    admin_info = connection.get_user_name_surname("users", current_user.id)
    admin_info = {"name": admin_info[0], "surname": admin_info[1]}

    if request.method == "POST":
        image = request.files.get("image")
        # image_path = event_info["image"]
        logger.log("info", f"image: {image}")

        if image.filename and image.filename != "":
            try:
                logger.log("info", f"Removing: static/{event_info["image"]}")

                os.remove(f"static/{event_info["image"]}")
                open(f"static/img/events/{image.filename}", "a").close()
                image.save(f"static/img/events/{image.filename}")
                image_path = f"img/events/{image.filename}"
            except Exception as e:
                logger.log("error", f"Removing: static/{event_info["image"]} failed! Full error: {e}")

                image_path = f"img/events/{image.filename}"
        else:
            image_path = event_info["image"]
            pass

        event_title = request.form.get("title")
        event_datetime = datetime.strptime(request.form.get("datetime"), "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
        event_type = request.form.get("type")
        event_content = request.form.get("content")
        event_participants = request.form.get("participants")

        logger.log("info", f"Path to new event image {image_path}")

        
        connection.update_event("events", event_type=event_type,
                                title=event_title, 
                                datetime=event_datetime, 
                                content=event_content, 
                                image=image_path, 
                                participants=event_participants, 
                                old_title=event_info["title"])
        
        return redirect("/events_list")

    return render_template("admin_editor/edit_event.html", event_info=event_info, admin_info=admin_info)


# routes

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large")
    return redirect("/edit_profile")

# errors

if __name__ == "__main__":
    app.run(host='0.0.0.0')
    logger.stop()

# start point

