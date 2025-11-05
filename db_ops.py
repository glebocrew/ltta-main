from mariadb import Connection, Cursor
from utils.logger import Logger
from flask_login import UserMixin
import sys, os
import time

# imports

mariadb_logger = Logger("logs/mariadb.txt", __file__)

# logger

DEFAULT_AVATAR = "img/avatars/default.png"

# default user image


class MariaConnection:
    def __init__(self, connection_conf: dict):
        """
        A class to deal with MariaDB.
        While initialising, creates connection with it.
        :param connection_conf: {host, port, user, password, db}
        """
        self.conf = connection_conf
        self.mariaconnection = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Установка соединения с MariaDB"""
        try:
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Connecting to mariadb to {self.conf['host']}:{self.conf['port']}.",
            )
            self.mariaconnection = Connection(**self.conf)
            self.mariaconnection.autocommit = True
            self.cursor = self.mariaconnection.cursor()

            # Устанавливаем таймауты для предотвращения разрыва соединения
            self.cursor.execute("SET SESSION wait_timeout = 28800")
            self.cursor.execute("SET SESSION interactive_timeout = 28800")
            self.cursor.execute("SET SESSION net_read_timeout = 600")
            self.cursor.execute("SET SESSION net_write_timeout = 600")

            mariadb_logger.log("info", f"Successfully connected to database.")
        except Exception as e:
            mariadb_logger.log(
                "error",
                f"Connection to mariadb was not established: arguments are not correct. Full exception: {e}",
            )
            mariadb_logger.log(
                "fatal", f"MariaDB module (.py) was stopped. Read logs upper."
            )
            sys.exit(2)

    def ensure_connection(self):
        """Проверка и восстановление соединения при необходимости"""
        try:
            # Простая проверка соединения
            self.cursor.execute("SELECT 1")
            return True
        except Exception as e:
            mariadb_logger.log(
                "warning", f"Connection lost, reconnecting... Error: {e}"
            )
            try:
                if self.mariaconnection:
                    self.mariaconnection.close()
                self.connect()
                return True
            except Exception as reconnect_error:
                mariadb_logger.log("error", f"Reconnection failed: {reconnect_error}")
                return False

    def execute_with_reconnect(self, query, params=None):
        """Выполнение запроса с автоматическим восстановлением соединения"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                return True
            except Exception as e:
                if (
                    "server has gone away" in str(e).lower()
                    or "connection" in str(e).lower()
                    or attempt < max_retries - 1
                ):
                    mariadb_logger.log(
                        "warning",
                        f"Connection issue detected (attempt {attempt + 1}), reconnecting: {e}",
                    )
                    if self.ensure_connection():
                        time.sleep(0.5)  # Небольшая задержка
                        continue
                else:
                    mariadb_logger.log("error", f"Query execution error: {e}")
                    return False
        return False

    def test(self):
        """
        Test query
        """
        if self.execute_with_reconnect(self.queries["test"]):
            self.cursor.fetchall()

    def select_all(self, table_name: str):
        """
        Selecting all from some table
        :param table_name: name of table you want to select
        """
        mariadb_logger.log("info", f"[{os.getpid()}] Selecting all from {table_name}")
        query = self.queries["select_all"].replace("table_name", table_name)

        if self.execute_with_reconnect(query):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully selected all from {table_name}"
            )
            return self.cursor.fetchall()
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Selecting all from {table_name} failed!"
            )
            return None

    def find_user_by_username(self, table_name: str, username: str):
        """
        Returns True if user was found.
        Returns False if user was not found.

        :param table_name: name of table you want to select
        :param username: username of user
        """
        query = self.queries["find_user_by_username"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (username,)):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully looked for user in {table_name}"
            )
            return bool(self.cursor.fetchone())
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Finding user in {table_name} failed!"
            )
            return False

    def find_user_by_email(self, table_name: str, email: str):
        """
        Returns True if email was found.
        Returns False if email was not found.

        :param table_name: name of table you want to select
        :param email: email of user
        """
        query = self.queries["find_user_by_email"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (email,)):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully looked for email in {table_name}"
            )
            return bool(self.cursor.fetchone())
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Finding email in {table_name} failed!"
            )
            return False

    def find_user_by_login_and_password(
        self, table_name: str, username: str, password: str
    ):
        """
        Returns True if user was found.
        Returns False if user was not found.

        :param table_name: name of table you want to select
        :param username: username of user
        :param password: password of user
        """
        query = self.queries["find_user_by_login_and_password"].replace(
            "table_name", table_name
        )

        if self.execute_with_reconnect(query, (username, password)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully looked for user by username and password in {table_name}",
            )
            return bool(self.cursor.fetchone())
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Finding user by username and password in {table_name} failed!",
            )
            return False

    def get_user_role_by_username(self, table_name: str, username: str):
        """
        Gets user role by his username

        :param table_name: name of table you want to find from
        :param username: username of user

        Returns -1 if user not exists. If exists returns his role.
        """
        query = self.queries["get_user_role_by_username"].replace(
            "table_name", table_name
        )

        if self.execute_with_reconnect(query, (username,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully got user role by email in {table_name}",
            )
            role = self.cursor.fetchone()
            return role if role else -1
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Getting user role by username in {table_name} failed!",
            )
            return -1

    def delete_user_by_id(self, table_name: str, id: str):
        """
        Drops profile by id

        :param table_name: name of table you want to delete from
        :param id: id of user
        """
        query = self.queries["delete_user_by_id"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (id,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully dropped user by id in {table_name}",
            )
            return True
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Dropping user by id in {table_name} failed!"
            )
            return False

    def drop_temp_profile_by_email(self, table_name: str, email: str):
        """
        Drops temp profile by email

        :param table_name: name of table you want to delete from
        :param email: email of user
        """
        query = self.queries["drop_temp_profile_by_email"].replace(
            "table_name", table_name
        )

        if self.execute_with_reconnect(query, (email,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully dropped temp user by email in {table_name}",
            )
            return True
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Dropping for temp user by email in {table_name} failed!",
            )
            return False

    def insert_new_temp_profile(
        self,
        table_name: str,
        username: str,
        code: str,
        datetime: str,
        email: str,
        name: str,
        surname: str,
        grade: int,
        faculty: str,
        password: str,
    ):
        """
        Inserts new temp profile

        :param table_name: name of table you want to insert
        :param username: username of user
        :param code: code of user
        :param datetime: when the code was given
        :param email: email of user
        :param name: name of user
        :param surname: surname of user
        :param grade: grade of user
        :param faculty: faculty of user

        """
        query = self.queries["insert_new_temp_profile"].replace(
            "table_name", table_name
        )

        if self.execute_with_reconnect(
            query,
            (email, code, datetime, name, surname, grade, faculty, username, password),
        ):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully inserted a temp user in {table_name}",
            )
            return True
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Inserting user by username and password in {table_name} failed!",
            )
            return False

    def get_temp_profile_by_email(self, table_name: str, email: str):
        """
        Gets temp profile by email

        :param table_name: name of table you want to select
        :param email: email of user

        Returns -1 if exception
        Returns all temp user information by email
        """
        query = self.queries["get_temp_profile_by_email"].replace(
            "table_name", table_name
        )

        if self.execute_with_reconnect(query, (email,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully looked for temp user by email in {table_name}",
            )
            return self.cursor.fetchone()
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Looking for temp user by email in {table_name} failed!",
            )
            return -1

    def create_new_user(
        self,
        table_name: str,
        username: str,
        name: str,
        surname: str,
        email: str,
        password: str,
        grade: str,
        faculty: str,
        id: str,
    ):
        """
        Creates new user
        :param table_name: name of table you want to insert
        :param username: username of user
        :param name: name of user
        :param surname: surname of user
        :param email: email of user
        :param password: password of user
        :param grade: grade of user
        :param faculty:  faculty of user INSERT INTO users (username, name, surname, email, password, rating, role, grade, faculty, avatar) VALUES (?, ?, ?, ?, ?, 0, 'user', ?, ?, ?);
        :param id: id of user
        """
        query = self.queries["create_new_user"].replace("table_name", table_name)

        if self.execute_with_reconnect(
            query,
            (
                username,
                name,
                surname,
                email,
                password,
                grade,
                faculty,
                DEFAULT_AVATAR,
                id,
            ),
        ):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully added user in {table_name}"
            )
            return True
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Adding user in {table_name} failed!"
            )
            return False

    def get_user_by_username(self, table_name: str, username: str):
        """
        Finds all user infomation by his username

        :param table_name: name of table you want to select
        :param username: username of user

        Returns dict with this user information:
        Username, Name, Surname, Email, Password, Rating, Role, Grade, Faculty, Avatar, Id
        """
        query = self.queries["get_user_by_username"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (username,)):
            user_info = self.cursor.fetchone()
            if user_info:
                mapped_user_info = {
                    "username": username,
                    "name": user_info[1],
                    "surname": user_info[2],
                    "email": user_info[3],
                    "password": user_info[4],
                    "rating": user_info[5],
                    "role": user_info[6],
                    "grade": user_info[7],
                    "faculty": user_info[8],
                    "avatar": user_info[9],
                    "id": user_info[10],
                }
                mariadb_logger.log(
                    "info", f"[{os.getpid()}] Succesfully got user in {table_name}"
                )
                return mapped_user_info
        return -1

    def get_user_by_id(self, table_name: str, id: str):
        """
        Finds all user infomation by his id

        :param table_name: name of table you want to select
        :param id: id of user

        Returns dict with this user information:
        Username, Name, Surname, Email, Password, Rating, Role, Grade, Faculty, Avatar, Id
        """
        query = self.queries["get_user_by_id"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (id,)):
            user_info = self.cursor.fetchone()
            if user_info:
                mapped_user_info = {
                    "username": user_info[0],
                    "name": user_info[1],
                    "surname": user_info[2],
                    "email": user_info[3],
                    "password": user_info[4],
                    "rating": user_info[5],
                    "role": user_info[6],
                    "grade": user_info[7],
                    "faculty": user_info[8],
                    "avatar": user_info[9],
                    "id": user_info[10],
                }
                mariadb_logger.log(
                    "info", f"[{os.getpid()}] Succesfully got user in {table_name}"
                )
                return mapped_user_info
        return -1

    def update_profile(
        self,
        table_name: str,
        username: str,
        name: str,
        surname: str,
        email: str,
        grade: int,
        faculty: str,
        avatar: str,
        old_username: str,
    ):
        """
        Updates updatable fields

        :param table_name: name of table you want to insert
        :param username: username of user
        :param name: name of user
        :param surname: surname of user
        :param email: email of user
        :param grade: grade of user
        :param faculty:  faculty of user
        :param avatar: avatar of user
        :param old_username: old username of user
        """
        query = self.queries["update_profile"].replace("table_name", table_name)

        if self.execute_with_reconnect(
            query,
            (username, name, surname, email, grade, faculty, avatar, old_username),
        ):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully updated user in {table_name}"
            )
            return True
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Updating user in {table_name} failed!"
            )
            return False

    def admin_update_profile(
        self,
        table_name: str,
        username: str,
        name: str,
        surname: str,
        email: str,
        grade: int,
        faculty: str,
        avatar: str,
        rating: float,
        role: str,
        old_username: str,
    ):
        """
        Updates updatable fields

        :param table_name: name of table you want to insert
        :param username: username of user
        :param name: name of user
        :param surname: surname of user
        :param email: email of user
        :param grade: grade of user
        :param faculty:  faculty of user
        :param avatar: avatar of user
        :param rating: rating of user
        :param role: role of user
        :param old_username: old username of user
        """
        query = self.queries["admin_update_profile"].replace("table_name", table_name)

        if self.execute_with_reconnect(
            query,
            (
                username,
                name,
                surname,
                email,
                grade,
                faculty,
                avatar,
                rating,
                role,
                old_username,
            ),
        ):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully updated user in {table_name}"
            )
            return True
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Updating user in {table_name} failed!"
            )
            return False

    def get_all_users(self, table_name: str):
        """
        Return all users from table

        :param table_name: name of table you want to select
        """
        query = self.queries["get_all_users"].replace("table_name", table_name)

        if self.execute_with_reconnect(query):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully selected all from {table_name}"
            )
            raw_info = self.cursor.fetchall()
            info = []
            for user in raw_info:
                temp_dict = {}
                temp_dict["username"] = user[0]
                temp_dict["name"] = user[1]
                temp_dict["surname"] = user[2]
                temp_dict["email"] = user[3]
                temp_dict["rating"] = user[5]
                temp_dict["role"] = user[6]
                temp_dict["grade"] = user[7]
                temp_dict["faculty"] = user[8]
                temp_dict["avatar"] = user[9]
                temp_dict["id"] = user[10]
                info.append(temp_dict)
            return info
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Selecting all from {table_name} failed!"
            )
            return []

    def get_user_name_surname(self, table_name: str, id: str):
        """
        Updates updatable fields

        :param table_name: name of table you want to select
        :param id: id of user
        """
        query = self.queries["get_user_name_surname"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (id,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully selected name surname from {table_name}",
            )
            info = self.cursor.fetchone()
            return info if info else -1
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Selecting name surname from {table_name} failed!",
            )
            return -1

    def create_event(
        self,
        table_name: str,
        type: str,
        title: str,
        datetime: str,
        content: str,
        image: str,
        id: str,
    ):
        """
        Creates new event

        :param table_name: name of table you want to select
        :param type: type of event
        :param title: title of event
        :param datetime: datetime of event
        :param content: content of event
        :param image: image of event
        :param id: id of event
        """
        query = self.queries["create_event"].replace("table_name", table_name)

        if self.execute_with_reconnect(
            query, (type, title, datetime, content, image, id)
        ):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully created event in {table_name}"
            )
            return True
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Creating event in {table_name} failed!"
            )
            return False

    def get_all_events(self, table_name: str):
        """
        Return all events from table

        :param table_name: name of table you want to select
        """
        query = self.queries["get_all_events"].replace("table_name", table_name)

        if self.execute_with_reconnect(query):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully selected all from {table_name}"
            )
            raw_info = self.cursor.fetchall()
            info = []
            for user in raw_info:
                temp_dict = {}
                temp_dict["type"] = user[0]
                temp_dict["title"] = user[1]
                temp_dict["datetime"] = user[2]
                temp_dict["content"] = user[3]
                temp_dict["image"] = user[4]
                temp_dict["participants"] = user[5]
                temp_dict["id"] = user[6]
                info.append(temp_dict)
            return info
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Selecting all from {table_name} failed!"
            )
            return []

    def get_all_finished_events(self, table_name: str):
        """
        Return all finished events from table

        :param table_name: name of table you want to select
        """
        query = self.queries["get_all_events"].replace("table_name", table_name)

        if self.execute_with_reconnect(query):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully selected all from {table_name}"
            )
            raw_info = self.cursor.fetchall()
            info = []
            for user in raw_info:
                temp_dict = {}
                temp_dict["type"] = user[0]
                temp_dict["title"] = user[1]
                temp_dict["datetime"] = user[2]
                temp_dict["content"] = user[3]
                temp_dict["image"] = user[4]
                temp_dict["participants"] = user[5]
                temp_dict["id"] = user[6]
                temp_dict["winners"] = user[7]
                info.append(temp_dict)
            return info
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Selecting all from {table_name} failed!"
            )
            return []

    def delete_event_by_id(self, table_name: str, id: str):
        """
        Deletes event by id

        :param table_name: name of table you want to delete from
        :param id: id of event
        """
        query = self.queries["delete_event_by_title"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (id,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully deleted event by id from {table_name}",
            )
            return True
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Deleting event by id from {table_name} failed!",
            )
            return False

    def get_event_by_title(self, table_name: str, title: str):
        """
        Gets event info by title

        :param table_name: name of table you want to select
        :param title: title of event
        """
        query = self.queries["get_event_by_title"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (title,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully got event info by title from {table_name}",
            )
            raw_info = self.cursor.fetchone()
            if raw_info:
                info = {}
                info["type"] = raw_info[0]
                info["title"] = raw_info[1]
                info["datetime"] = raw_info[2]
                info["content"] = raw_info[3]
                info["image"] = raw_info[4]
                info["participants"] = raw_info[5]
                info["id"] = raw_info[6]
                return info
        return -1

    def get_finished_event_by_title(self, table_name: str, title: str):
        """
        Gets finished event info by title

        :param table_name: name of table you want to select
        :param title: title of event
        """
        query = self.queries["get_event_by_title"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (title,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully got event info by title from {table_name}",
            )
            raw_info = self.cursor.fetchone()
            if raw_info:
                info = {}
                info["type"] = raw_info[0]
                info["title"] = raw_info[1]
                info["datetime"] = raw_info[2]
                info["content"] = raw_info[3]
                info["image"] = raw_info[4]
                info["participants"] = raw_info[5]
                info["id"] = raw_info[6]
                info["winners"] = raw_info[7]
                return info
        return -1

    def get_event_id_by_title(self, table_name: str, title: str):
        """
        Gets event id by title

        :param table_name: name of table you want to delete from
        :param title: title of event
        """
        query = self.queries["get_event_id_by_title"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (title,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully got event id by title from {table_name}",
            )
            info = self.cursor.fetchone()
            return info[0] if info else -1
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Getting event id by title from {table_name} failed!",
            )
            return -1

    def update_event(
        self,
        table_name: str,
        event_type: str,
        title: str,
        datetime: str,
        content: str,
        image: str,
        participants: int,
        old_title: str,
    ):
        """
        Updates updatable fields

        :param table_name: name of table you want to insert
        :param title: title of event
        :param datetime: datetime of event
        :param content: content of event
        :param image: path to image of event
        :param participants: participants of event
        :param old_title: old_title of event
        """
        query = self.queries["update_event"].replace("table_name", table_name)

        if self.execute_with_reconnect(
            query,
            (event_type, title, datetime, content, image, participants, old_title),
        ):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully updated event in {table_name}"
            )
            return True
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Updating event in {table_name} failed!"
            )
            return False

    def append_participant(
        self, table_name: str, participant_id: str, event_title: str
    ):
        """Updates updatable fields

        :param table_name: name of table you want to insert

        :param participant_id: participan id you want to append
        :param event_title: title of event
        """
        query = self.queries["append_participant"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (participant_id, event_title)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully appended participant in event in {table_name}",
            )
            return True
        else:
            mariadb_logger.log(
                "error",
                f"[{os.getpid()}] Appending participant in event in {table_name} failed!",
            )
            return False

    def get_participants_by_title(self, table_name: str, title: str):
        """Gets participants by event title

        :param table_name: name of table you want to insert

        :param participant_id: participan id you want to append
        :param event_title: title of event
        """
        query = self.queries["get_participants_by_title"].replace(
            "table_name", table_name
        )

        if self.execute_with_reconnect(query, (title,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully got all participants by event title from {table_name}",
            )
            raw_info = self.cursor.fetchone()
            if raw_info and raw_info[0]:
                return raw_info[0].split(sep=",")
        return []

    def get_matches_by_title(self, table_name: str, title: str):
        """Gets all matches by event title

        :param table_name: name of table you want to select

        :param event_title: title of event
        """
        query = self.queries["get_matches_by_title"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (title,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully got all matches by event title from {table_name}",
            )
            raw_info = self.cursor.fetchall()
            info = []
            for match in raw_info:
                temp_match = {}
                temp_match["title"] = match[0]
                temp_match["player1"] = self.get_user_by_id("users", match[1])[
                    "username"
                ]
                temp_match["player2"] = self.get_user_by_id("users", match[2])[
                    "username"
                ]
                temp_match["winner"] = match[3]
                if temp_match["winner"] != "None":
                    temp_match["winner"] = self.get_user_by_id("users", match[3])[
                        "username"
                    ]
                temp_match["score"] = match[4]
                info.append(temp_match)
            return info
        return []

    def get_matches_by_id(self, table_name: str, id: str):
        """Gets all matches by event id

        :param table_name: name of table you want to select

        :param id: id of event
        """
        query = self.queries["get_matches_by_id"].replace("table_name", table_name)

        if self.execute_with_reconnect(query, (id,)):
            mariadb_logger.log(
                "info",
                f"[{os.getpid()}] Succesfully got all matches by event id from {table_name}",
            )
            raw_info = self.cursor.fetchall()
            info = []
            for match in raw_info:
                temp_match = {}
                temp_match["title"] = match[0]
                temp_match["player1"] = self.get_user_by_id("users", match[1])[
                    "username"
                ]
                temp_match["player2"] = self.get_user_by_id("users", match[2])[
                    "username"
                ]
                temp_match["winner"] = match[3]
                if temp_match["winner"] != "None":
                    temp_match["winner"] = self.get_user_by_id("users", match[3])[
                        "username"
                    ]
                temp_match["score"] = match[4]
                info.append(temp_match)
            return info
        return []

    def wrap_matches(self, table_name: str, matches: list, id: str):
        query_clear = self.queries["clear_matches"].replace("table_name", table_name)
        query_create = self.queries["create_match"].replace("table_name", table_name)

        if self.execute_with_reconnect(query_clear, (id,)):
            for match in matches:
                mariadb_logger.log("debug", f"{match['player1']} {match['player2']}")
                player1_id = self.get_user_by_username("users", match["player1"])["id"]
                player2_id = self.get_user_by_username("users", match["player2"])["id"]
                winner_id = (
                    match["winner"]
                    if match["winner"] == "None"
                    else self.get_user_by_username("users", match["winner"])["id"]
                )

                if not self.execute_with_reconnect(
                    query_create,
                    (match["title"], player1_id, player2_id, winner_id, match["score"]),
                ):
                    mariadb_logger.log("error", f"Failed to create match: {match}")
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Succesfully wrapped matches in {table_name}"
            )
            return True
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Wrapping matches in {table_name} failed!"
            )
            return False

    def create_finished_event(
        self,
        table_name: str,
        event_type: str,
        title: str,
        datetime: str,
        content: str,
        image: str,
        participants: str,
        id: str,
        winners: str,
    ):
        """
        Creates new finished event

        :param table_name: name of table you want to select
        :param event_type: type of event
        :param title: title of event
        :param datetime: datetime of event
        :param content: content of event
        :param image: image of event
        :param id: id of event
        :param winners: winners of event
        """
        query = self.queries["create_finished_event"].replace("table_name", table_name)

        if self.execute_with_reconnect(
            query,
            (event_type, title, datetime, content, image, participants, id, winners),
        ):
            # Если это соревнование - обновляем рейтинги по системе RTTF
            if event_type == "соревнование":
                self.calculate_rttf_rating(id, winners)

            mariadb_logger.log(
                "info", f"[{os.getpid()}] Successfully created event in {table_name}"
            )
            return True
        else:
            mariadb_logger.log(
                "error", f"[{os.getpid()}] Creating event in {table_name} failed!"
            )
            return False

    def calculate_rttf_rating(self, event_id: str, winners: str):
        """
        Calculate RTTF rating for table tennis competition
        Based on Russian Table Tennis Federation rating system

        :param event_id: ID of the finished event
        :param winners: comma-separated string of winner IDs (1st,2nd,3rd)
        """
        try:
            # Get the finished event data
            query = "SELECT participants, winners FROM finished_events WHERE id = ?"
            if self.execute_with_reconnect(query, (event_id,)):
                event_data = self.cursor.fetchone()
                if not event_data:
                    return False

                participants = [
                    pid for pid in event_data[0].split(",") if pid and pid != "None"
                ]
                winners_list = [
                    wid for wid in event_data[1].split(",") if wid and wid != "None"
                ]

                if not participants:
                    return True  # No participants, nothing to calculate

                # Get current ratings of all participants
                participants_ratings = {}
                for participant_id in participants:
                    user_query = "SELECT rating FROM users WHERE id = ?"
                    if self.execute_with_reconnect(user_query, (participant_id,)):
                        rating_data = self.cursor.fetchone()
                        if rating_data:
                            participants_ratings[participant_id] = rating_data[0]
                        else:
                            participants_ratings[participant_id] = (
                                1000  # Default rating for new players
                            )

                # Calculate RTTF rating changes
                rating_changes = self._calculate_rttf_points(
                    participants_ratings, winners_list
                )

                # Apply rating changes
                for participant_id, change in rating_changes.items():
                    update_query = "UPDATE users SET rating = rating + ? WHERE id = ?"
                    self.execute_with_reconnect(update_query, (change, participant_id))

                mariadb_logger.log(
                    "info", f"Successfully updated RTTF ratings for event {event_id}"
                )
                return True

        except Exception as e:
            mariadb_logger.log("error", f"RTTF rating calculation failed: {e}")
            return False

    def _calculate_rttf_points(self, participants_ratings: dict, winners: list):
        """
        Calculate RTTF rating points based on Russian Table Tennis Federation system

        :param participants_ratings: dict of {player_id: current_rating}
        :param winners: list of winner IDs in order [1st, 2nd, 3rd]
        :return: dict of {player_id: rating_change}
        """
        rating_changes = {}
        player_count = len(participants_ratings)

        if player_count < 2:
            return rating_changes  # Need at least 2 players

        # RTTF coefficients based on tournament size
        k_factor = self._get_rttf_k_factor(player_count)

        # Calculate expected scores and actual results
        for player_id, rating in participants_ratings.items():
            expected_score = 0
            actual_score = 0

            # Calculate expected score against all opponents
            for opponent_id, opponent_rating in participants_ratings.items():
                if player_id != opponent_id:
                    expected_score += self._expected_result(rating, opponent_rating)

            # Calculate actual score based on final position
            player_position = self._get_player_position(
                player_id, winners, participants_ratings
            )
            actual_score = self._get_actual_score(player_position, player_count)

            # Calculate rating change
            rating_change = k_factor * (actual_score - expected_score)
            rating_changes[player_id] = round(rating_change)

        return rating_changes

    def _get_rttf_k_factor(self, player_count: int):
        """
        Get K-factor based on RTTF rules and tournament size
        """
        if player_count >= 16:
            return 40  # Large tournament
        elif player_count >= 8:
            return 30  # Medium tournament
        else:
            return 20  # Small tournament

    def _expected_result(self, rating_a: int, rating_b: int):
        """
        Calculate expected result using Elo formula
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def _get_player_position(self, player_id: str, winners: list, all_players: dict):
        """
        Determine player's final position
        """
        if winners and len(winners) >= 1 and player_id == winners[0]:
            return 1  # 1st place
        elif winners and len(winners) >= 2 and player_id == winners[1]:
            return 2  # 2nd place
        elif winners and len(winners) >= 3 and player_id == winners[2]:
            return 3  # 3rd place
        else:
            # For other players, sort by rating to determine position
            sorted_players = sorted(
                all_players.items(), key=lambda x: x[1], reverse=True
            )
            for position, (pid, _) in enumerate(sorted_players, 1):
                if pid == player_id:
                    return position
                return len(all_players)  # Last place

    def _get_actual_score(self, position: int, total_players: int):
        """
        Calculate actual score based on final position (RTTF scoring system)
        """
        if position == 1:
            return 0.95  # 1st place
        elif position == 2:
            return 0.85  # 2nd place
        elif position == 3:
            return 0.75  # 3rd place
        elif position <= total_players * 0.1:  # Top 10%
            return 0.65
        elif position <= total_players * 0.25:  # Top 25%
            return 0.55
        elif position <= total_players * 0.5:  # Top 50%
            return 0.45
        else:
            return 0.35  # Bottom 50%

    def get_events_ids_by_user_id(self, table_name: str, id: str):
        """
        Gets events

        :param table_name: name of table you want to select
        :param id: id of event
        """
        query = self.queries["get_events_ids_by_user_id"].replace(
            "table_name", table_name
        )

        if self.execute_with_reconnect(query, (id,)):
            mariadb_logger.log(
                "info", f"[{os.getpid()}] Getting all about event by id in {table_name}"
            )
            raw_info = self.cursor.fetchall()
            info = []
            for event in raw_info:
                event_info = {
                    "type": event[0],
                    "title": event[1],
                    "datetime": event[2],
                    "content": event[3],
                    "image": event[4],
                    "participants": event[5],
                }
                info.append(event_info)
            return info
        return []
    
    def remove_participant(self, table_name: str, participant_id: str, event_title: str):
        """
        Removes participant from event
        
        :param table_name: name of table you want to update
        :param participant_id: participant id to remove
        :param event_title: title of event
        """
        # First get current participants
        query_get = self.queries["get_participants_by_title"].replace("table_name", table_name)
        
        if self.execute_with_reconnect(query_get, (event_title,)):
            current_participants = self.cursor.fetchone()
            if current_participants and current_participants[0]:
                # Remove the participant from the list
                participants_list = current_participants[0].split(',')
                if participant_id in participants_list:
                    participants_list.remove(participant_id)
                    updated_participants = ','.join(participants_list)
                    
                    # Update the event with new participants list
                    query_update = "UPDATE table_name SET participants = ? WHERE title = ?".replace("table_name", table_name)
                    
                    if self.execute_with_reconnect(query_update, (updated_participants, event_title)):
                        mariadb_logger.log(
                            "info", 
                            f"[{os.getpid()}] Successfully removed participant {participant_id} from event {event_title}"
                        )
                        return True
        
        mariadb_logger.log(
            "error", 
            f"[{os.getpid()}] Failed to remove participant {participant_id} from event {event_title}"
        )
        return False

    # Словарь запросов остается без изменений
    queries = {
        "test": "SHOW DATABASES;",
        "select_all": "SELECT * FROM table_name;",
        "find_user_by_username": "SELECT * FROM table_name WHERE username = ?;",
        "find_user_by_email": "SELECT * FROM table_name WHERE email = ?;",
        "find_user_by_login_and_password": "SELECT * FROM table_name WHERE username = ? AND password = ?;",
        "insert_new_temp_profile": "INSERT INTO table_name (email, code, datetime, name, surname, grade, faculty, username, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
        "delete_user_by_id": "DELETE FROM table_name WHERE id = ?;",
        "get_temp_profile_by_email": "SELECT * FROM table_name WHERE email = ?;",
        "drop_temp_profile_by_email": "DELETE FROM table_name WHERE email = ?;",
        "create_new_user": "INSERT INTO table_name (username, name, surname, email, password, rating, role, grade, faculty, avatar, id) VALUES (?, ?, ?, ?, ?, 0, 'user', ?, ?, ?, ?);",
        "get_user_by_username": "SELECT * FROM table_name WHERE username = ?;",
        "get_user_by_id": "SELECT * FROM table_name WHERE id = ?;",
        "update_profile": "UPDATE table_name SET username = ?, name = ?, surname = ?, email = ?, grade = ?, faculty = ?, avatar = ? WHERE username = ?;",
        "admin_update_profile": "UPDATE table_name SET username = ?, name = ?, surname = ?, email = ?, grade = ?, faculty = ?, avatar = ?, rating = ?, role = ? WHERE username = ?;",
        "get_user_role_by_username": "SELECT role FROM table_name WHERE username = ?;",
        "get_all_users": "SELECT * FROM table_name ORDER BY rating DESC;",
        "get_user_name_surname": "SELECT name, surname FROM table_name WHERE id = ?",
        "create_event": "INSERT INTO table_name (type, title, datetime, content, image, participants, id) VALUES (?, ?, ?, ?, ?, '', ?);",
        "get_all_events": "SELECT * FROM table_name;",
        "delete_event_by_title": "DELETE FROM table_name WHERE id = ?;",
        "get_event_by_title": "SELECT * FROM table_name WHERE title = ?;",
        "update_event": "UPDATE table_name SET type = ?, title = ?, datetime = ?, content = ?, image = ?, participants = ? WHERE title = ?;",
        "append_participant": "UPDATE table_name SET participants = CONCAT(participants, ',', ?) WHERE title = ?",
        "get_participants_by_title": "SELECT participants FROM table_name WHERE title = ?;",
        "get_event_id_by_title": "SELECT id FROM table_name WHERE title = ?;",
        "get_events_ids_by_user_id": "SELECT * FROM table_name WHERE participants LIKE CONCAT('%', ?, '%');",
        "get_matches_by_title": "SELECT * FROM table_name WHERE title = ?;",
        "get_matches_by_id": "SELECT * FROM table_name WHERE id = ?;",
        "clear_matches": "DELETE FROM table_name WHERE id = ?;",
        "create_match": "INSERT INTO table_name (id, player1, player2, winner, score) VALUES (?, ?, ?, ?, ?)",
        "create_finished_event": "INSERT INTO table_name (type, title, datetime, content, image, participants, id, winners) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    }


class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role
