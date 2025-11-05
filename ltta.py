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
import time

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
login_manager.login_view = "login"
login_manager.login_message = (
    "Пожалуйста, войдите в учётную запись для просмотра этой страницы."
)

# flask app conf

logger = Logger("logs/logs.txt", __file__)

# logger conf

# email conf


def safe_db_operation(operation, *args, **kwargs):
    """Безопасное выполнение операций с БД с автоматическим восстановлением"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = operation(*args, **kwargs)
            return result
        except Exception as e:
            if (
                "server has gone away" in str(e).lower()
                or "connection" in str(e).lower()
            ) and attempt < max_retries - 1:
                logger.log(
                    "warning",
                    f"Database connection lost, retrying... Attempt {attempt + 1}",
                )
                try:
                    # Пересоздаем соединение
                    global connection
                    connection = MariaConnection(json_conf["db"])
                    time.sleep(1)  # Небольшая задержка перед повторной попыткой
                except Exception as reconnect_error:
                    logger.log("error", f"Reconnection failed: {reconnect_error}")
                    continue
            else:
                logger.log("error", f"Database operation failed: {e}")
                raise e
    return None


try:
    logger.log("info", f"[{os.getpid()}] Loading mariadb configure.")
    json_conf = load(open("conf.json"))
    connection = MariaConnection(json_conf["db"])
    logger.log("info", f"[{os.getpid()}] Successfully loaded mariadb confs.")
except:
    logger.log("error", f"[{os.getpid()}] There are no database configure file.")
    logger.log(
        "fatal",
        f"[{os.getpid()}] The main app was stopped since there're no mariadb confs.",
    )
    sys.exit(1)

# mariadb conf


@login_manager.user_loader
def load_user(id):
    try:
        user_data = safe_db_operation(connection.get_user_by_id, "users", id)
        if user_data != -1:
            user_role = user_data["role"]
        else:
            user_role = "user"
    except Exception as e:
        logger.log("error", f"Error while loading user: {e}")
        user_role = "user"
    return User(id, user_role)


@app.route("/")
def index():
    try:
        # Простая проверка соединения
        safe_db_operation(connection.test)
    except Exception as e:
        logger.log("error", f"Error while connecting to mariadb: {e}")
        return render_template("index.html", db_error=True)

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password_hash = sha256(request.form.get("password").encode("utf-8")).hexdigest()

        try:
            user_exists = safe_db_operation(
                connection.find_user_by_login_and_password,
                "users",
                username,
                password_hash,
            )

            if user_exists:
                user_data = safe_db_operation(
                    connection.get_user_by_username, "users", username
                )
                if user_data and user_data != -1:
                    user = User(user_data["id"], user_data["role"])
                    login_user(user)
                    logger.log("info", f"new SUCCESFULL login: username={username}")
                    flash("Вы успешно авторизованы!")
                    return redirect(url_for("index"))

            flash("Неверные данные! Если у вас нет аккаунта, зарегистрируйте его.")
            return redirect("login")

        except Exception as e:
            logger.log("error", f"Login error: {e}")
            flash("Ошибка соединения с базой данных. Попробуйте позже.")
            return redirect("login")

    return render_template("login.html")


@app.route("/registration", methods=["GET", "POST"])
def registration():
    faculties = load(open("conf.json"))["faculties"]

    if request.method == "POST":
        username = request.form.get("username")

        if safe_db_operation(connection.find_user_by_username, "users", username):
            flash("Этот ник уже занят!")
            return redirect("registration")

        password = sha256()
        password.update(request.form.get("password").encode("utf-8"))

        repeat_password = sha256()
        repeat_password.update(request.form.get("repeat_password").encode("utf-8"))

        password = password.hexdigest()
        repeat_password = repeat_password.hexdigest()

        name = request.form.get("name")
        surname = request.form.get("surname")

        if password != repeat_password:
            flash("Пароли не совпадают")
            return redirect("registration")

        email = request.form.get("email")

        if safe_db_operation(connection.find_user_by_email, "users", email):
            flash("Этот email уже занят!")
            return redirect("registration")

        grade = request.form.get("grade")

        faculty = request.form.get("faculty")

        if grade not in ["8", "9", "10", "11"] or grade == "":
            flash("Вы не ввели класс!")
            return redirect("registration")

        if faculty not in faculties or faculty == "":
            flash("Вы не ввели факультет!")
            return redirect("registration")

        code = "".join(secrets.choice("0123456789") for _ in range(6))

        logger.log(
            "info",
            f"New registration detected: {username} {email} {name} {surname} {grade} {faculty}",
        )

        try:
            logger.log("info", f"[{os.getpid()}] Loading email configure.")
            json_conf = load(open("conf.json"))

            port = json_conf["mailbox"]["port"]
            smtp_server = json_conf["mailbox"]["smtp_server"]
            sender_email = json_conf["mailbox"]["sender_email"]
            password_smtp = json_conf["mailbox"]["password"]
            message_html = open(
                "templates/email/email.html", "r", encoding="utf-8"
            ).read()

            context = ssl._create_unverified_context()

            server = smtplib.SMTP_SSL(smtp_server, port, context=context)

            server.login(sender_email, password_smtp)

            logger.log("info", f"[{os.getpid()}] Successfully loaded mailbox conofs.")
        except Exception as e:
            logger.log(
                "error",
                f"[{os.getpid()}] There are no mailbox configure file (or the syntax is incorrect).",
            )
            logger.log(
                "fatal",
                f"[{os.getpid()}] The main app was stopped since there're no mailbox confs. Fill exception: {e}",
            )
            sys.exit(1)

        message = MIMEMultipart("alternative")
        message.attach(
            MIMEText(
                message_html.replace("VERIFICATION_CODE", f"{code}"), "html", "utf-8"
            )
        )
        message["From"] = "LTTA TEAM <ltta@glebocrew.ru>"
        message["Subject"] = "Your Verification Code"
        message["To"] = f"{name} {surname} <{email}>"

        try:
            server.sendmail(sender_email, email, message.as_string())
            logger.log("info", f"Sending verification code to {email}.")

            safe_db_operation(
                connection.insert_new_temp_profile,
                "codes",
                username,
                code,
                datetime.now(),
                email,
                name,
                surname,
                grade,
                faculty,
                password,
            )
        except smtplib.SMTPSenderRefused or smtplib.SMTPRecipientsRefused as e:
            logger.log(
                "error",
                f"Sending code on {email} failed because of its incorrectance! Full error {e}.",
            )
            return render_template("registration.html", message="Некорректный email!")

        except smtplib.SMTPServerDisconnected as e:
            logger.log(
                "error",
                f"SMTP server was disconnected! Trying to reconnect! Full error {e}",
            )
            return render_template("registration.html", message="Некорректный email!")

        server.quit()
        return redirect(url_for("verification", email=email))

    return render_template("registration.html", faculties=faculties)


@app.route("/verification/<email>", methods=["GET", "POST"])
def verification(email):
    if request.method == "POST":
        temp_user = safe_db_operation(
            connection.get_temp_profile_by_email, "codes", email
        )
        if temp_user == -1:
            flash("Время действия кода истекло. Попробуйте снова!")
            return redirect("/registration")

        code_time = datetime.strptime(temp_user[2], "%Y-%m-%d %H:%M:%S.%f")

        if (datetime.now() - code_time).total_seconds() > 300:
            flash("Время действия кода истекло. Попробуйте снова!")
            return redirect("/registration")

        if str(request.form.get("code")) == temp_user[1]:
            safe_db_operation(
                connection.create_new_user,
                "users",
                temp_user[7],
                temp_user[3],
                temp_user[4],
                temp_user[0],
                temp_user[8],
                temp_user[5],
                temp_user[6],
                uuid.uuid4(),
            )
            safe_db_operation(connection.drop_temp_profile_by_email, "codes", email)
            flash("Учетная запись подтверждена! Для использования кабинета - войдите в него.")
            return redirect("/login")
        else:
            flash("Код неверный. Попробуйте снова!")
            return redirect(url_for("verification", email=email))

    return render_template("verification.html", email=email)


@app.route("/profile")
@login_required
def profile():
    try:
        user_data = safe_db_operation(
            connection.get_user_by_id, "users", current_user.id
        )
        user_events = safe_db_operation(
            connection.get_events_ids_by_user_id, "events", current_user.id
        )
        username_len = len(user_data["username"]) if user_data != -1 else 0

        if user_data != -1:
            return render_template(
                "profile.html",
                can_edit=True,
                user_data=user_data,
                user_events=user_events,
                username_len=username_len,
                logo_path="/icons/svg/goldball.svg",
            )
        else:
            flash("Профиль не найден")
            return redirect("/")
    except Exception as e:
        logger.log("error", f"Profile error: {e}")
        flash("Ошибка загрузки профиля")
        return redirect("/")


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    try:
        faculties = load(open("conf.json"))["faculties"]
        user_data = safe_db_operation(
            connection.get_user_by_id, "users", current_user.id
        )
        if user_data == -1:
            flash("Профиль не найден")
            return redirect("/profile")

        if request.method == "POST":
            avatar = request.files.get("avatar")
            logger.log("info", f"avatar: {avatar}")

            if avatar and avatar.filename != "":
                extention = avatar.filename[-3:]
                if user_data["avatar"].split(sep="/")[-1] != "default.png":
                    logger.log("info", f"Updating avatar for {user_data['username']}.")

                    to_delete = glob.glob(
                        f"static/img/avatars/{user_data['username']}.*"
                    )
                    logger.log("info", f"Deleting previous avatars aka {to_delete}.")

                    if to_delete:
                        for file in to_delete:
                            os.remove(file)
                            logger.log("info", f"Deleting {file}")
                try:
                    logger.log(
                        "info", f"Creating file {user_data['username']}.{extention}"
                    )

                    avatar.save(
                        f"static/img/avatars/{user_data['username']}.{extention}"
                    )
                    user_data["avatar"] = (
                        f"img/avatars/{user_data['username']}.{extention}"
                    )

                    logger.log("info", "File successfully created")
                except Exception as e:
                    logger.log("error", f"File was not created! Full error: {e}")

            username = request.form.get("username")

            if (
                safe_db_operation(connection.find_user_by_username, "users", username)
                and username != user_data["username"]
            ):
                return render_template(
                    "edit_profile.html",
                    can_edit=True,
                    user_data=user_data,
                    message="Этот никнейм уже занят!",
                )

            if username != user_data["username"]:
                if user_data["avatar"].split("/")[-1] != "default.png":
                    user_avatars = glob.glob(
                        f"static/img/avatars/{user_data['username']}.*"
                    )
                    try:
                        logger.log("info", f"Renaming files caused by username change.")
                        for user_avatar in user_avatars:
                            logger.log("info", f"extention: {user_data['avatar'][-3:]}")
                            os.rename(
                                user_avatar,
                                f"static/img/avatars/{username}.{user_data['avatar'][-3:]}",
                            )
                        user_data["avatar"] = (
                            f"img/avatars/{username}.{user_data['avatar'][-3:]}"
                        )
                        logout_user()
                    except Exception as e:
                        logger.log("error", f"Renaming failed! Full error {e}")

            name = request.form.get("name")
            surname = request.form.get("surname")
            grade = request.form.get("grade")
            faculty = request.form.get("faculty")
            email = request.form.get("email")

            success = safe_db_operation(
                connection.update_profile,
                "users",
                username,
                name,
                surname,
                email,
                grade,
                faculty,
                user_data["avatar"],
                user_data["username"],
            )

            if success:
                return redirect("/profile")
            else:
                flash("Ошибка обновления профиля")
                return redirect("/edit_profile")

        return render_template(
            "edit_profile.html",
            can_edit=False,
            user_data=user_data,
            faculties=faculties,
        )

    except Exception as e:
        logger.log("error", f"Edit profile error: {e}")
        flash("Ошибка загрузки страницы")
        return redirect("/profile")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/ratings", methods=["GET", "POST"])
@login_required
def ratings():
    try:
        ratings = safe_db_operation(connection.get_all_users, "users")

        if request.method == "POST":
            return redirect(url_for("rating", user=request.form.get("username")))

        return render_template("ratings.html", ratings=ratings)
    except Exception as e:
        logger.log("error", f"Ratings error: {e}")
        flash("Ошибка загрузки рейтингов")
        return redirect("/")


@app.route("/rating/<user>", methods=["GET", "POST"])
def rating(user):
    try:
        user_data = safe_db_operation(connection.get_user_by_username, "users", user)

        if user_data == -1:
            return "<h1>There's no such user</h1>", 404

        if request.method == "POST":
            create_card(
                f"static/{user_data['avatar']}",
                user_data["username"],
                user_data["name"],
                user_data["surname"],
                user_data["rating"],
                user_data["grade"],
                user_data["faculty"],
                user_data["id"],
            )

            return send_file(
                f"user_cards/{user_data['id']}.pdf",
                as_attachment=True,
                download_name=f"{user_data['username']}.pdf",
            )

        return render_template(
            "profile.html",
            can_edit=False,
            user_data=user_data,
            username_len=len(user_data["username"]),
        )
    except Exception as e:
        logger.log("error", f"Rating error: {e}")
        flash("Ошибка загрузки рейтинга")
        return redirect("/ratings")


@app.route("/members", methods=["GET", "POST"])
@login_required
def members():
    try:
        logger.log(
            "info", f"Trying to get in admin page: {current_user.id, current_user.role}"
        )
        if "admin" in current_user.role:
            members = safe_db_operation(connection.get_all_users, "users")

            if request.method == "POST":
                action = request.form.get("action")

                if action == "edit":
                    logger.log(
                        "info", f"Building url for {request.form.get('username')}"
                    )
                    return redirect(
                        url_for("member", user=request.form.get("username"))
                    )
                elif action == "delete":
                    logger.log("debug", f"{request.form.get('id')}")
                    user_role = safe_db_operation(
                        connection.get_user_role_by_username,
                        "users",
                        safe_db_operation(
                            connection.get_user_by_id, "users", request.form.get("id")
                        )["username"],
                    )

                    if user_role and user_role[0] == "admin":
                        flash("Вы не можете удалять администраторов")
                        return redirect("members")

                    safe_db_operation(
                        connection.delete_user_by_id, "users", request.form.get("id")
                    )
                    logger.log("debug", f"{request.form.get('id')}")
                    return redirect("members")

            return render_template("admin/members.html", members=members)
        else:
            return redirect("/")
    except Exception as e:
        logger.log("error", f"Members error: {e}")
        flash("Ошибка загрузки списка пользователей")
        return redirect("/")


@app.route("/member/<user>")
@login_required
def member(user):
    try:
        user_data = safe_db_operation(connection.get_user_by_username, "users", user)
        return render_template(
            "admin/profile_admin_view.html",
            user_data=user_data,
            username_len=len(user_data["username"]),
        )
    except Exception as e:
        logger.log("error", f"Member error: {e}")
        flash("Ошибка загрузки профиля")
        return redirect("/members")


@app.route("/member/<user>/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile_admin(user):
    try:
        user_data = safe_db_operation(connection.get_user_by_username, "users", user)

        # Получаем данные текущего администратора
        admin_data = safe_db_operation(
            connection.get_user_by_id, "users", current_user.id
        )
        if admin_data == -1:
            flash("Ошибка: администратор не найден")
            return redirect("/members")

        # Создаем словарь с именем и фамилией администратора
        admin_name_surname = {
            "name": admin_data.get("name", ""),
            "surname": admin_data.get("surname", ""),
        }

        if request.method == "POST":
            # Проверяем подтверждение администратора
            confirmation_name = request.form.get("admin_confirmation", "").strip()
            expected_confirmation = (
                f"{admin_name_surname['name']} {admin_name_surname['surname']}"
            )

            # if confirmation_name != expected_confirmation:
            #     flash("Подтверждение неверно. Введите ваше имя и фамилию для подтверждения изменений.")
            #     return render_template("admin/edit_profile_admin_view.html",
            #                            user_data=user_data,
            #                            admin_name_surname=admin_name_surname,
            #                            faculties=load(open("conf.json"))["faculties"])

            if "admin" not in user_data["role"]:
                avatar = request.files.get("avatar")
                extention = avatar.filename[-3:] if avatar and avatar.filename else ""

                logger.log("info", f"avatar: {avatar}")

                if avatar and avatar.filename != "":
                    if user_data["avatar"].split(sep="/")[-1] != "default.png":
                        logger.log(
                            "info", f"Updating avatar for {user_data['username']}."
                        )
                        to_delete = glob.glob(
                            f"static/img/avatars/{user_data['username']}.*"
                        )
                        logger.log(
                            "info", f"Deleting previous avatars aka {to_delete}."
                        )

                        if to_delete:
                            for file in to_delete:
                                os.remove(file)
                                logger.log("info", f"Deleting {file}")
                    try:
                        logger.log(
                            "info", f"Creating file {user_data['username']}.{extention}"
                        )
                        avatar.save(
                            f"static/img/avatars/{user_data['username']}.{extention}"
                        )
                        user_data["avatar"] = (
                            f"img/avatars/{user_data['username']}.{extention}"
                        )
                        logger.log("info", "File successfully created")
                    except Exception as e:
                        logger.log("error", f"File was not created! Full error: {e}")

                username = request.form.get("username")

                if (
                    safe_db_operation(
                        connection.find_user_by_username, "users", username
                    )
                    and username != user_data["username"]
                ):
                    return render_template(
                        "admin/edit_profile_admin_view.html",
                        user_data=user_data,
                        admin_name_surname=admin_name_surname,
                        faculties=load(open("conf.json"))["faculties"],
                        message="Этот никнейм уже занят!",
                    )

                if username != user_data["username"]:
                    if user_data["avatar"].split("/")[-1] != "default.png":
                        user_avatars = glob.glob(
                            f"static/img/avatars/{user_data['username']}.*"
                        )
                        try:
                            logger.log(
                                "info", f"Renaming files caused by username change."
                            )
                            for user_avatar in user_avatars:
                                logger.log(
                                    "info", f"extention: {user_data['avatar'][-3:]}"
                                )
                                os.rename(
                                    user_avatar,
                                    f"static/img/avatars/{username}.{user_data['avatar'][-3:]}",
                                )
                            user_data["avatar"] = (
                                f"img/avatars/{username}.{user_data['avatar'][-3:]}"
                            )
                        except Exception as e:
                            logger.log("error", f"Renaming failed! Full error {e}")

                name = request.form.get("name")
                surname = request.form.get("surname")
                grade = int(request.form.get("grade"))
                faculty = request.form.get("faculty")
                role = request.form.get("role")
                rating = request.form.get("rating")
                email = request.form.get("email")

                success = safe_db_operation(
                    connection.admin_update_profile,
                    "users",
                    username,
                    name,
                    surname,
                    email,
                    grade,
                    faculty,
                    user_data["avatar"],
                    rating,
                    role,
                    user_data["username"],
                )

                if success:
                    return redirect(url_for("member", user=username))
                else:
                    flash("Ошибка обновления профиля")
            else:
                flash("Нельзя редактировать администратора!")
                return redirect("/members")

        return render_template(
            "admin/edit_profile_admin_view.html",
            user_data=user_data,
            admin_name_surname=admin_name_surname,
            username_len=len(user_data["username"]),
            faculties=load(open("conf.json"))["faculties"],
        )
    except Exception as e:
        logger.log("error", f"Edit profile admin error: {e}")
        flash("Ошибка загрузки страницы")
        return redirect("/members")


@app.route("/events_list", methods=["GET", "POST"])
@login_required
def events_list():
    try:
        if "user" in current_user.role:
            return redirect("/")

        events = safe_db_operation(connection.get_all_events, "events")

        if request.method == "POST":
            event_title = request.form.get("event_title").strip()
            if request.form.get("action") == "edit":
                return redirect(url_for("edit_event", event=event_title))
            elif request.form.get("action") == "delete":
                event_id = safe_db_operation(
                    connection.get_event_id_by_title, "events", event_title
                )
                safe_db_operation(connection.delete_event_by_id, "events", event_id)

                # Поиск и удаление изображения события
                for event in events:
                    if event["title"] == event_title:
                        path = f"static/{event['image']}"
                        try:
                            logger.log("info", f"Deleting old event image {path}")
                            os.remove(path)
                        except Exception as e:
                            logger.log(
                                "error",
                                f"Deleting old event image {path} failed! Full error {e}",
                            )
                        break

                return redirect("events_list")

        return render_template("admin_editor/events_list.html", events=events)
    except Exception as e:
        logger.log("error", f"Events list error: {e}")
        flash("Ошибка загрузки списка событий")
        return redirect("/")


@app.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    try:
        if "user" in current_user.role:
            return redirect("/")

        if request.method == "POST":
            event_type = request.form.get("type")
            title = request.form.get("title").strip()
            content = request.form.get("content")
            datetime_form = request.form.get("datetime")
            datetime_form = datetime.strptime(datetime_form, "%Y-%m-%dT%H:%M")
            image = request.files.get("image")

            if not image or not image.filename:
                flash("Пожалуйста, загрузите изображение")
                return render_template("admin_editor/create_event.html")

            ext = (
                image.filename.rsplit(".", 1)[1].lower()
                if "." in image.filename
                else "png"
            )
            unique_filename = f"{uuid.uuid4()}.{ext}"
            image_path = f"static/img/events/{unique_filename}"

            try:
                logger.log("info", f"Сохранение изображения события в {image_path}")
                image.save(image_path)
                success = safe_db_operation(
                    connection.create_event,
                    "events",
                    event_type,
                    title,
                    datetime_form,
                    content,
                    f"img/events/{unique_filename}",
                    uuid.uuid4(),
                )
                if success:
                    return redirect("events_list")
                else:
                    flash("Ошибка создания события")
            except Exception as e:
                logger.log("error", f"Ошибка сохранения изображения: {e}")
                flash("Ошибка при сохранении изображения")

        return render_template("admin_editor/create_event.html")
    except Exception as e:
        logger.log("error", f"Create event error: {e}")
        flash("Ошибка создания события")
        return redirect("/events_list")


@app.route("/edit_event/<event>", methods=["GET", "POST"])
@login_required
def edit_event(event):
    try:
        if "users" in current_user.role:
            return redirect("/")

        event_info = safe_db_operation(connection.get_event_by_title, "events", event)
        if event_info == -1:
            flash("Событие не найдено")
            return redirect("/events_list")

        event_info["datetime"] = datetime.strptime(
            event_info["datetime"], "%Y-%m-%d %H:%M:%S"
        )
        participants_list = [
            safe_db_operation(connection.get_user_by_id, "users", participant)[
                "username"
            ]
            for participant in event_info["participants"].split(sep=",")
            if participant != ""
        ]

        matches = safe_db_operation(
            connection.get_matches_by_id,
            "matches",
            safe_db_operation(
                connection.get_event_id_by_title, "events", event_info["title"]
            ),
        )

        # event_info["datetime"] = event_info["datetime"].strftime("%Y-%m-%dT%H:%M")
        admin_info = safe_db_operation(
            connection.get_user_name_surname, "users", current_user.id
        )
        admin_info = (
            {"name": admin_info[0], "surname": admin_info[1]}
            if admin_info != -1
            else {"name": "", "surname": ""}
        )

        if request.method == "POST":
            if request.form.get("action") == "changes":
                image = request.files.get("image")
                image_path = event_info["image"]

                logger.log("d", request.form.get("counter"))

                if image and image.filename != "":
                    try:
                        # Удаляем старое изображение только если оно не дефолтное
                        if event_info["image"] and "default" not in event_info["image"]:
                            logger.log(
                                "info", f"Removing: static/{event_info['image']}"
                            )
                            os.remove(f"static/{event_info['image']}")

                        # Сохраняем новое изображение
                        ext = (
                            image.filename.rsplit(".", 1)[1].lower()
                            if "." in image.filename
                            else "png"
                        )
                        unique_filename = f"{uuid.uuid4()}.{ext}"
                        image_path = f"img/events/{unique_filename}"
                        image.save(f"static/{image_path}")
                    except Exception as e:
                        logger.log("error", f"Image handling error: {e}")
                        flash("Ошибка при обработке изображения")
                        image_path = event_info[
                            "image"
                        ]  # Возвращаем старое изображение при ошибке

                # Сохраняем существующих участников и добавляем новых
                existing_participants = event_info[
                    "participants"
                ]  # Сохраняем текущих участников
                new_participants = request.form.get("participants", "")

                # Объединяем старых и новых участников (убираем дубликаты)
                all_participants = set()
                if existing_participants:
                    all_participants.update(existing_participants.split(","))
                if new_participants:
                    all_participants.update(new_participants.split(","))

                # Убираем пустые значения
                all_participants = [p for p in all_participants if p]
                participants_ids_str = ",".join(all_participants)

                event_title = request.form.get("title")
                event_datetime = datetime.strptime(
                    request.form.get("datetime"), "%Y-%m-%dT%H:%M"
                ).strftime("%Y-%m-%d %H:%M:%S")
                event_type = request.form.get("type")
                event_content = request.form.get("content")
                event_participants = request.form.get("participants")
                event_id = safe_db_operation(
                    connection.get_event_id_by_title, "events", event_title
                )

                matches = []
                for id in range(int(request.form.get("counter"))):
                    if request.form.get(f"player1-{id}"):
                        matches.append(
                            {
                                "title": event_id,
                                "player1": request.form.get(f"player1-{id}"),
                                "player2": request.form.get(f"player2-{id}"),
                                "winner": request.form.get(f"winner-{id}"),
                                "score": request.form.get(f"score-{id}"),
                                "id": event_id,
                            }
                        )

                participants_ids = participants_ids_str
                for participant in event_participants.split(sep=","):
                    if participant != "":
                        user_data = safe_db_operation(
                            connection.get_user_by_username, "users", participant
                        )
                        if user_data != -1:
                            participants_ids += user_data["id"] + ","

                success = safe_db_operation(
                    connection.update_event,
                    "events",
                    event_type,
                    event_title,
                    event_datetime,
                    event_content,
                    image_path,
                    participants_ids,
                    event_info["title"],
                )

                if success:
                    safe_db_operation(
                        connection.wrap_matches, "matches", matches, event_id
                    )
                    return redirect("/events_list")
                else:
                    flash("Ошибка обновления события")

            elif request.form.get("action") == "finish":
                if event_info["type"] == "соревнование":
                    # Получаем победителей для RTTF системы
                    winner1 = request.form.get("winner1")
                    winner2 = request.form.get("winner2")
                    winner3 = request.form.get("winner3")

                    winners = []
                    if winner1 and winner1 != "None":
                        winner1_data = safe_db_operation(
                            connection.get_user_by_username, "users", winner1
                        )
                    if winner1_data != -1:
                        winners.append(winner1_data["id"])

                    if winner2 and winner2 != "None":
                        winner2_data = safe_db_operation(
                            connection.get_user_by_username, "users", winner2
                        )
                    if winner2_data != -1:
                        winners.append(winner2_data["id"])

                    if winner3 and winner3 != "None":
                        winner3_data = safe_db_operation(
                            connection.get_user_by_username, "users", winner3
                        )
                    if winner3_data != -1:
                        winners.append(winner3_data["id"])

                    # Формируем строку победителей
                    winners_str = ",".join(winners)

                    # Формируем список участников
                    participants_ids = ""
                    participant_count = 0
                    for participant in event_info["participants"].split(sep=","):
                        if participant != "":
                            user_data = safe_db_operation(
                                connection.get_user_by_id, "users", participant
                            )
                            if user_data != -1:
                                participants_ids += user_data["id"] + ","
                                participant_count += 1

                    # Проверяем минимальное количество участников для RTTF
                    if participant_count < 2:
                        flash("Для расчета рейтинга RTTF нужно минимум 2 участника")
                        return redirect(url_for("edit_event", event=event))

                    # Создаем завершенное событие (рейтинг RTTF автоматически рассчитается)
                    success = safe_db_operation(
                        connection.create_finished_event,
                        "finished_events",
                        event_info["type"],
                        event_info["title"],
                        event_info["datetime"],
                        event_info["content"],
                        event_info["image"],
                        participants_ids,
                        event_info["id"],
                        winners_str,
                    )

                    if success:
                        safe_db_operation(
                            connection.delete_event_by_id, "events", event_info["id"]
                        )
                        safe_db_operation(
                            connection.wrap_matches, "matches", [], event_info["id"]
                        )

                        flash(
                            "Соревнование завершено! Рейтинги RTTF рассчитаны и обновлены."
                        )
                        return redirect("/events_list")
                    else:
                        flash("Ошибка завершения события")

        logger.log("d", f"Event time is: {event_info["datetime"]}")
        return render_template(
            "admin_editor/edit_event.html",
            event_info=event_info,
            admin_info=admin_info,
            matches=matches,
            counter=len(matches),
            participants_list=participants_list,
        )
    except Exception as e:
        logger.log("error", f"Edit event error: {e}")
        flash("Ошибка редактирования события")
        return redirect("/events_list")


@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    try:
        events = safe_db_operation(connection.get_all_events, "events")
        finished_events = safe_db_operation(
            connection.get_all_events, "finished_events"
        )

        if request.method == "POST":
            if request.form.get("action") == "view":
                event_title = request.form.get("event_title")
                return redirect(url_for("event", event=event_title))
            elif request.form.get("action") == "view_finished":
                event_title = request.form.get("event_title")
                return redirect(url_for("finished_event", event=event_title))

        return render_template(
            "events.html", events=events, finished_events=finished_events
        )
    except Exception as e:
        logger.log("error", f"Events error: {e}")
        flash("Ошибка загрузки событий")
        return redirect("/")


@app.route("/event/<event>", methods=["GET", "POST"])
@login_required
def event(event):
    try:
        event_data = safe_db_operation(connection.get_event_by_title, "events", event)
        if event_data == -1:
            return "<h1>This event doesn't exist. Try to update your page.</h1>", 404

        participants = safe_db_operation(
            connection.get_participants_by_title, "events", event
        )

        # Check if current user is registered for this event
        is_registered = str(current_user.id) in participants if participants else False

        if request.method == "POST":
            action = request.form.get("action")
            
            if action == "register":
                # Register for event
                safe_db_operation(
                    connection.append_participant, "events", current_user.id, event
                )
                # flash("Вы успешно зарегистрировались на событие!")
                
            elif action == "unregister":
                # Unregister from event
                success = safe_db_operation(
                    connection.remove_participant, "events", str(current_user.id), event
                )
                # if success:
                #     flash("Вы успешно отменили регистрацию на событие!")
                # else:
                #     flash("Ошибка при отмене регистрации")
            
            return redirect(url_for("event", event=event))

        return render_template(
            "event.html",
            event=event_data,
            participants=participants,
            current_user_id=current_user.id,
            is_registered=is_registered
        )
    except Exception as e:
        logger.log("error", f"Event error: {e}")
        flash("Ошибка загрузки события")
        return redirect("/events")
    

def download_finished_event(event_data, participants, winners):
    """
    Создает PDF-карточку завершенного события для скачивания

    :param event_data: словарь с данными о завершенном событии
    :param participants: список участников события
    :param winners: список победителей
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Читаем HTML шаблон для завершенных событий
    template_path = "templates/event_card/event_card.html"

    with open(template_path, "r", encoding="utf-8") as f:
        html_markup = f.read()

    # Заменяем плейсхолдеры на реальные данные
    html_markup = html_markup.replace("EVENT_TITLE", event_data.get("title", "Событие"))
    html_markup = html_markup.replace(
        "EVENT_TYPE", event_data.get("type", "Мероприятие")
    )
    html_markup = html_markup.replace("EVENT_DATE", str(event_data.get("datetime", "")))
    html_markup = html_markup.replace(
        "EVENT_CONTENT", event_data.get("content", "Описание отсутствует")
    )

    # Форматируем список победителей
    winners_html = ""
    if winners:
        for i, winner in enumerate(winners, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            winners_html += f"<p>{medal} {i}. {winner}</p>"
    else:
        winners_html = "<p>Победители не определены</p>"

    html_markup = html_markup.replace("WINNERS_LIST", winners_html)

    # Форматируем список участников
    participants_html = ""
    if participants:
        for i, participant in enumerate(participants, 1):
            participants_html += f"<p>{i}. {participant}</p>"
    else:
        participants_html = "<p>Участники отсутствуют</p>"

    html_markup = html_markup.replace("PARTICIPANTS_LIST", participants_html)

    # Создаем безопасное имя файла
    safe_title = "".join(
        c
        for c in event_data.get("title", "event")
        if c.isalnum() or c in (" ", "-", "_")
    ).rstrip()
    filename = f"{safe_title}_finished.pdf"
    filepath = f"event_cards/{filename}"

    # Создаем директорию если не существует
    os.makedirs("event_cards", exist_ok=True)

    # Генерируем PDF
    try:
        HTML(string=html_markup, base_url=base_dir).write_pdf(
            filepath, stylesheets=[CSS(string="@page { size: A4; margin: 20mm; }")]
        )
        logger.log("info", f"Successfully generated finished event PDF: {filename}")
        return filename
    except Exception as e:
        logger.log("error", f"Error generating finished event PDF: {e}")
        return create_fallback_pdf(event_data, filename)


@app.route("/finished_event/<event>", methods=["GET", "POST"])
@login_required
def finished_event(event):
    try:
        event_data = safe_db_operation(
            connection.get_finished_event_by_title, "finished_events", event
        )
        if event_data == -1:
            return "<h1>This event doesn't exist. Try to update your page.</h1>", 404

        event_participants = []
        for participant in event_data["participants"].split(sep=","):
            if participant:
                try:
                    user_data = safe_db_operation(
                        connection.get_user_by_id, "users", participant
                    )
                    if user_data != -1:
                        full_name = f"{user_data['name']} {user_data['surname']}"
                        event_participants.append(full_name)
                except Exception as e:
                    logger.log("error", f"{e}")

        # Получаем информацию о победителях
        winners = []
        if event_data.get("winners"):
            for winner in event_data["winners"].split(sep=","):
                if winner:
                    try:
                        winner_data = safe_db_operation(
                            connection.get_user_by_id, "users", winner
                        )
                        if winner_data != -1:
                            winner_name = (
                                f"{winner_data['name']} {winner_data['surname']}"
                            )
                            winners.append(winner_name)
                    except Exception as e:
                        logger.log("error", f"Error getting winner data: {e}")

        if request.method == "POST":
            # Создаем карточку завершенного события для скачивания
            filename = download_finished_event(event_data, event_participants, winners)
            return send_file(
                f"event_cards/{filename}",
                as_attachment=True,
                download_name=f"{event}.pdf",
            )

        return render_template(
            "finished_event.html",
            event=event_data,
            participants=event_participants,
            winners=winners,
            current_user_id=current_user.id,
        )
    except Exception as e:
        logger.log("error", f"Finished event error: {e}")
        flash("Ошибка загрузки завершенного события")
        return redirect("/events")


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.errorhandler(413)
def request_entity_too_large(error):
    flash("Файл слишком большой")
    return redirect("/edit_profile")


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>Forbidden page</h1>", 404


@app.errorhandler(500)
def internal_server_error(e):
    logger.log("error", f"Internal server error: {e}")
    return "<h1>Internal server error. Please try again later.</h1>", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0")
    logger.stop()
