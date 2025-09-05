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

from downloads import *
import downloads

## pdfs

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
import uuid


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
def load_user(id):
    return User(id, connection.get_user_by_id("users", id)["role"])



@app.route("/")
def index():
    try:
        connection.test()
    except Exception as e:
        logger.log("error", f"Error while connecting to mariadb. Full error {e}. Restarting...")
        try:
            connection = MariaConnection(json_conf["db"])
        except Exception as e:
            logger.log("fatal", "Mariadb args are incorrect")
            sys.exit(0)


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
        try:
            if connection.find_user_by_login_and_password("users", username, password):
                user = User(connection.get_user_by_username("users", username)["id"], connection.get_user_role_by_username("users", username))
                login_user(user)
                logger.log("info", f"new SUCCESFULL login: username={username} password={password}")

                return redirect(url_for("index"))
            else:
                flash("Неверные данные! Если у вас нет аккаунта, зарегистрируйте его.")
                return redirect("login") ## TODO: it's only if args are incorrect V COMPLETED
        except Exception as e:
            logger.log("info", f"Restarting mariadb...")
            connection = MariaConnection(json_conf["db"])

            if connection.find_user_by_login_and_password("users", username, password):
                user = User(connection.get_user_by_username("users", username)["id"], connection.get_user_role_by_username("users", username))
                login_user(user)
                logger.log("info", f"new SUCCESFULL login: username={username} password={password}")

                return redirect(url_for("index"))
            else:
                flash("Неверные данные! Если у вас нет аккаунта, зарегистрируйте его.")
                return redirect("login") 
                 ## TODO: it's only if args are incorrect V COMPLETED
            
        
    return render_template("login.html")

@app.route("/registration", methods = ['GET', 'POST'])
def registration():
    faculties = load(open("conf.json"))["faculties"]

    if request.method == 'POST':
        username = request.form.get("username") # TODO: if username is not in mariadb! V COMPLETED

        if connection.find_user_by_username("users", username):
            flash("Этот ник уже занят!")
            redirect("registration")
            
        password = sha256()
        password.update(request.form.get("password").encode("utf-8"))
        
        repeat_password = sha256()
        repeat_password.update(request.form.get("repeat_password").encode("utf-8"))

        password = password.hexdigest() 
        repeat_password = repeat_password.hexdigest() # TODO: if passwords match! V COMPLETED

        name = request.form.get("name")
        surname = request.form.get("surname")        

        if password != repeat_password:
            flash("Пароли не совпадают")
            redirect("registration")

        email = request.form.get("email") # TODO: if email is not in mariadb V COMPLETED

        if connection.find_user_by_email("users", email):
            flash("Этот email уже занят!")
            redirect("registration")

        grade = request.form.get("grade")

        faculty = request.form.get("faculty")

        if grade not in ["8","9","10","11"] or grade == "":
            flash("Вы не ввели класс!")
            return redirect("registration")

        if faculty not in faculties or faculty == "":
            flash("Вы не ввели факультет!")
            return redirect("registration")

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

    return render_template("registration.html", faculties=faculties)

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
            connection.create_new_user("users", temp_user[7], temp_user[3], temp_user[4], temp_user[0], temp_user[8], temp_user[5], temp_user[6], uuid.uuid4())
            connection.drop_temp_profile_by_email("codes", email)
            return redirect("/login")
        else:
            return redirect(url_for('verification', email=email))

    return render_template('verification.html', email=email)

@app.route("/profile")
@login_required
def profile():
    logger.log("info", f"{current_user.id}")
    user_data = connection.get_user_by_id("users", current_user.id)
    user_events = connection.get_events_ids_by_user_id("events", current_user.id)
    logger.log("info", f"{user_data}")
    if user_data != -1:
        return render_template("profile.html", user_data=user_data, user_events=user_events)
    
@app.route("/edit_profile", methods = ['GET', 'POST'])
@login_required
def edit_profile():
    user_data = connection.get_user_by_id("users", current_user.id)
    if user_data != -1:
        if request.method == 'POST':
            avatar = request.files.get("avatar")
            logger.log("info", f"avatar: {avatar}")

            if avatar and avatar.filename != "":
                extention = avatar.filename[-3:]
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

@app.route("/ratings", methods=['GET', 'POST'])
@login_required
def ratings():
    ratings = connection.get_all_users("users")

    if request.method == 'POST':
        return redirect(url_for("rating", user=request.form.get("username")))

    
    return render_template("ratings.html", ratings=ratings)

@app.route("/rating/<user>", methods=['GET', 'POST'])
def rating(user):
    user_data = connection.get_user_by_username("users", user)

    if user_data == -1:
        return "<h1>There's no such user", 404
    
    if request.method == 'POST':
        user_info = connection.get_user_by_username("users", user)

        create_card(f"static/{user_info['avatar']}", user_info["username"], user_info["name"], user_info["surname"], user_info["rating"], user_info["grade"], user_info["faculty"], user_info["id"])

        return send_file(f"user_cards/{user_info["id"]}.pdf", as_attachment=True, download_name=f"{user_info["username"]}.pdf")

    return render_template("rating.html", user_data=user_data)

@app.route("/members", methods=['GET', 'POST'])
@login_required
def members():
    logger.log("info", f"Trying to get in admin page: {current_user.id, current_user.role}")
    if 'admin' in current_user.role:
        members = connection.get_all_users("users")

        if request.method == 'POST':
            action = request.form.get("action")

            if action == "edit":
                logger.log("info", f"Building url for {request.form.get("username")}")
                return redirect(url_for("member", user=request.form.get("username")))
            elif action == "delete":
                logger.log("debug", f"{request.form.get('id')}")
                logger.log("debug", f"{connection.get_user_role_by_username("users", connection.get_user_by_id("users", request.form.get("id"))["username"])}")
                                                     
                if connection.get_user_role_by_username("users", connection.get_user_by_id("users", request.form.get("id"))["username"])[0] == "admin":
                    flash("You can't delete admins")
                    return redirect("members")
                  
                connection.delete_user_by_id("users", request.form.get("id"))
                logger.log("debug", f"{request.form.get('id')}")
                return redirect("members")

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
    if "user" in current_user.role:
        return redirect("/")
    # TODO: list of events display V COMPLETED
    events = connection.get_all_events("events")

    # logger.log("debug", f"{events[0]["datetime"]}")

    if request.method == 'POST':
        event_title = request.form.get("event_title").strip()
        if request.form.get("action") == "edit":
            return redirect(url_for("edit_event", event=event_title))
            pass
        elif request.form.get("action") == "delete":
            connection.delete_event_by_id("events", connection.get_event_id_by_title("events", event_title))
            
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
    
    if request.method == 'POST':
        event_type = request.form.get("type")
        title = request.form.get("title").strip()
        content = request.form.get("content")
        timezone = request.form.get("timezone")
        datetime_form = request.form.get("datetime")
        datetime_form = datetime.strptime(datetime_form, "%Y-%m-%dT%H:%M")
        image = request.files.get("image")

        if not image or not image.filename:
            flash("Пожалуйста, загрузите изображение")
            return render_template("admin_editor/create_event.html")

        # Генерируем уникальное имя файла
        ext = image.filename.rsplit('.', 1)[1].lower() if '.' in image.filename else 'png'
        unique_filename = f"{uuid.uuid4()}.{ext}"
        image_path = f"static/img/events/{unique_filename}"

        try:
            logger.log("info", f"Сохранение изображения события в {image_path}")
            image.save(image_path)
            connection.create_event("events", event_type, title, datetime_form, content, f"img/events/{unique_filename}", uuid.uuid4())
            return redirect("events_list")
        except Exception as e:
            logger.log("error", f"Ошибка сохранения изображения: {e}")
            flash("Ошибка при сохранении изображения")
            return render_template("admin_editor/create_event.html")

    return render_template("admin_editor/create_event.html")


@app.route("/edit_event/<event>", methods=['GET', 'POST'])
@login_required
def edit_event(event):
    if "users" in current_user.role:
        return redirect("/")
    

    event_info = connection.get_event_by_title("events", event)
    event_info["datetime"] = datetime.strptime(event_info["datetime"], "%Y-%m-%d %H:%M:%S")
    logger.log("debug", f"Participants: {event_info["participants"].split(sep=",")}")
    participants_list = [connection.get_user_by_id("users", participant)["username"] for participant in event_info["participants"].split(sep=",") if participant != ""]
    event_info["participants"] = [connection.get_user_by_id("users", participant)["username"] for participant in event_info["participants"].split(sep=",") if participant != ""]
    participants = ""
    for participant in event_info["participants"]:
        participants += participant + ","
    event_info["participants"] = participants
    event_info["participants"] = participants


    logger.log("debug", f"Participants: {event_info["participants"]}")
    matches = connection.get_matches_by_id("matches", connection.get_event_id_by_title("events", event_info['title']))
    
    logger.log("debug", matches)
    logger.log("debug", connection.get_event_id_by_title("events", event_info['title']))
    logger.log("debug", event_info['title'])
    # event_info["datetime"] = datetime.strptime(event_info["datetime"], "%Y-%m-%d %H:%M") + timedelta(hours=3)
    # event_info["datetime"] = datetime.strptime(event_info["datetime"], "%Y-%m-%d %H:%M:%S")
    event_info["datetime"] = event_info["datetime"].strftime("%Y-%m-%dT%H:%M")
    admin_info = connection.get_user_name_surname("users", current_user.id)
    admin_info = {"name": admin_info[0], "surname": admin_info[1]}
    if request.method == 'POST':
        if request.form.get("action") == "changes":
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
            event_id = connection.get_event_id_by_title("events", event_title)
            logger.log("info", f"Path to new event image {image_path}")
            matches = []
            for id in range(int(request.form.get("counter"))):
                if not request.form.get(f"player1-{id}"):
                    continue
                else:
                    matches.append({"title": event_id,
                                    "player1": request.form.get(f"player1-{id}"),
                                    "player2": request.form.get(f"player2-{id}"),
                                    "winner": request.form.get(f"winner-{id}"),
                                    "score": request.form.get(f"score-{id}"),
                                    "id": event_id
                                    })
            participants_ids = ""
            for participant in event_participants.split(sep=","):
                if participant != "":
                    participants += connection.get_user_by_username("users", participant)["id"] + ","
            event_participants = participants
            connection.wrap_matches("matches", matches, event_id)
            connection.update_event("events", event_type=event_type,
                                    title=event_title, 
                                    datetime=event_datetime, 
                                    content=event_content, 
                                    image=image_path, 
                                    participants=event_participants, 
                                    old_title=event_info["title"])
            return redirect("/events_list")
        elif request.form.get("action") == "finish":
            if event_info["type"] == "соревнование":
                logger.log("debug", f"{request.form.get("winner1")} {request.form.get("winner2")} {request.form.get("winner3")}")


                winner1_username = connection.get_user_by_username("users", request.form.get("winner1"))["id"]
                winner2_username = connection.get_user_by_username("users", request.form.get("winner2"))["id"]
                winner3_username = connection.get_user_by_username("users", request.form.get("winner3"))["id"]

                logger.log("debug", event_info["participants"])
                
                participants_ids = ""

                for participant in event_info["participants"].split(sep=","):                
                    if participant != "":
                        user_id = connection.get_user_by_username("users", participant)["id"]
                        participants_ids += user_id + ","
                                


                connection.create_finished_event("finished_events", event_info["type"], event_info["title"], event_info["datetime"], event_info["content"], event_info["image"], participants_ids, event_info["id"], f"{winner1_username},{winner2_username},{winner3_username}")
                connection.delete_event_by_id("events", event_info["id"])
            else:
                participants_ids = ""

                for participant in event_info["participants"].split(sep=","):                
                    if participant != "":
                        user_id = connection.get_user_by_username("users", participant)["id"]
                        participants_ids += user_id + ","
                        
                connection.create_finished_event("finished_events", event_type, event_title, event_datetime, event_content, image_path, participants_ids, id, f"not_championship")
                connection.delete_event_by_id("events", event_info["id"])

            connection.wrap_matches("matches", [], event_info["title"])
            return redirect("/events_list")
    return render_template("admin_editor/edit_event.html", event_info=event_info, admin_info=admin_info, matches=matches, counter=len(matches), participants_list=participants_list)



@app.route("/events", methods=['GET', 'POST'])
@login_required
def events():
    events = connection.get_all_events("events")
    finished_events = connection.get_all_events("finished_events")

    # logger.log("debug", f"{events[0]["datetime"]}")

    if request.method == 'POST':
        if request.form.get("action") == "view":
            event_title = request.form.get("event_title")
            return redirect(url_for("event", event=event_title))
        elif request.form.get("action") == "view_finished":
            event_title = request.form.get("event_title")
            return redirect(url_for("finished_event", event=event_title))
    
    return render_template("events.html", events=events, finished_events=finished_events)    

@app.route("/event/<event>", methods=['GET', 'POST'])
@login_required
def event(event):
    try:
        event_data = connection.get_event_by_title("events", event)

        participants = connection.get_participants_by_title("events", event)

        logger.log("debug", f"{event_data}")
    except:
        return "<h1>This event doesn't exist. Try to update your page.</h1>"


    if event_data != -1:

        if request.method == 'POST':
            event_title = request.form.get("event")
            connection.append_participant("events", current_user.id, event_title)

            return redirect("/events")

        return render_template("event.html", event=event_data, participants=participants, current_user_id=current_user.id)
    else:
        return "<h1>This event doesn't exist. Try to update your page.</h1>"

@app.route("/finished_event/<event>", methods=['GET', 'POST'])
@login_required
def finished_event(event):
    try:
        event_data = connection.get_finished_event_by_title("finished_events", event)
        logger.log("debug", f"{event_data}")

        participants = event_data["participants"]
        logger.log("debug", f"{participants}")
        
        event_participants = []
        for participant in participants.split(sep=","):
            if not participant: 
                continue
            
            try:
                user_data = connection.get_user_by_id("users", participant)
                full_name = f"{user_data['name']} {user_data['surname']}"
                event_participants.append(full_name)               
            except Exception as e:
                logger.log("error", f"{e}")
    except Exception as e:
        logger.log("error", f"{e}")
        return "<h1>This event doesn't exist. Try to update your page.</h1>"


    if event_data != -1:
        if request.method == 'POST':
            # TODO: return file with path/participants
            
            if event_data["type"] == "соревнование":
                matches = connection.get_matches_by_id("matches", event_data["id"])
                if current_user.id in event_participants:
                    pass
                else:
                    pass

            return redirect("/events")

        return render_template("finished_event.html", event=event_data, participants=event_participants, current_user_id=current_user.id)
    else:
        return "<h1>This event doesn't exist. Try to update your page.</h1>"


# routes

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large")
    return redirect("/edit_profile")


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>Forbidden page</h1>", 404

# errors

if __name__ == "__main__":
    app.run(host='0.0.0.0')
    logger.stop()

# start point

