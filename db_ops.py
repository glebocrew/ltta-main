from mariadb import Connection, Cursor
from utils.logger import Logger
from flask_login import UserMixin
import sys, os

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

        try:
            mariadb_logger.log("info", f"[{os.getpid()}] Connecting to mariadb to {self.conf["host"]}:{self.conf["port"]}.")
            self.mariaconnection = Connection(**self.conf)
            self.mariaconnection.autocommit = True

            mariadb_logger.log("info", f"Successfully connected to database.")
        except Exception as e:
            mariadb_logger.log("error", f"Connection to mariadb was not established: arguments are not correct. Full exception: {e}")
            mariadb_logger.log("fatal", f"MariaDB module (.py) was stopped. Read logs upper.")
            sys.exit(2)
        
        self.cursor = Cursor(self.mariaconnection)
        self.queries = {
            "select_all": "SELECT * FROM table_name;",
            "find_user_by_username": "SELECT * FROM table_name WHERE username = ?;",
            "find_user_by_email": "SELECT * FROM table_name WHERE email = ?;",
            "find_user_by_login_and_password": "SELECT * FROM table_name WHERE username = ? AND password = ?;",
            "insert_new_temp_profile": "INSERT INTO table_name (email, code, datetime, name, surname, grade, faculty, username, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",

            "get_temp_profile_by_email": "SELECT * FROM table_name WHERE email = ?;",
            "drop_temp_profile_by_email": "DELETE FROM table_name WHERE email = ?;",

            "create_new_user": "INSERT INTO table_name (username, name, surname, email, password, rating, role, grade, faculty, avatar) VALUES (?, ?, ?, ?, ?, 0, 'user', ?, ?, ?);",
            "get_user_by_username": "SELECT * FROM table_name WHERE username = ?;",
            "update_profile": "UPDATE table_name SET username = ?, name = ?, surname = ?, email = ?, grade = ?, faculty = ?, avatar = ? WHERE username = ?;",

            "admin_update_profile": "UPDATE table_name SET username = ?, name = ?, surname = ?, email = ?, grade = ?, faculty = ?, avatar = ?, rating = ?, role = ? WHERE username = ?;",
            "get_user_role_by_username": "SELECT role FROM table_name WHERE username = ?;",
            "get_all_users": "SELECT * FROM table_name",
            "get_user_name_surname": "SELECT name, surname FROM table_name WHERE username = ?",

            "create_event": "INSERT INTO table_name (type, title, datetime, content, image, participants) VALUES (?, ?, ?, ?, ?, '');",
            "get_all_events": "SELECT * FROM table_name;",
            "delete_event_by_title": "DELETE FROM table_name WHERE title = ?;",
            "get_event_by_title": "SELECT * FROM table_name WHERE title = ?;",
            "update_event": "UPDATE table_name SET type = ?, title = ?, datetime = ?, content = ?, image = ?, participants = ? WHERE title = ?;"
        }

    def select_all(self, table_name: str):
        """
        Selecting all from some table
        :param table_name: name of table you want to select
        """
        mariadb_logger.log("info", f"[{os.getpid()}] Selecting all from {table_name}")
        try:
            self.cursor.execute(self.queries["select_all"].replace("table_name", table_name))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully selected all from {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Selecting all from {table_name} failed! Full error: {e}")

        return self.cursor.fetchall()
    
    def find_user_by_username(self, table_name: str, username: str):
        """
        Returns True if user was found.
        Returns False if user was not found.

        :param table_name: name of table you want to select
        :param username: username of user
        """
        try:
            self.cursor.execute(self.queries["find_user_by_username"].replace("table_name", table_name), (username,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully looked for user in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Finding user in {table_name} failed! Full error: {e}")

        if self.cursor.fetchone():
            return True
        else:
            return False
        
    def find_user_by_email(self, table_name: str, email: str):
        """
        Returns True if email was found.
        Returns False if email was not found.

        :param table_name: name of table you want to select
        :param email: email of user
        """
        try:
            self.cursor.execute(self.queries["find_user_by_email"].replace("table_name", table_name), (email,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully looked for email in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Finding email in {table_name} failed! Full error: {e}")
        
        
        if self.cursor.fetchone():
            return True
        else:
            return False
        
    def find_user_by_login_and_password(self, table_name: str, username: str, password: str):
        """
        Returns True if user was found.
        Returns False if user was not found.

        :param table_name: name of table you want to select
        :param username: username of user
        :param password: password of user
        """
        try:
            self.cursor.execute(self.queries["find_user_by_login_and_password"].replace("table_name", table_name), (username, password,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully looked for user by username and password in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Inserting temp user in {table_name} failed! Full error: {e}")
        
        
        if self.cursor.fetchone():
            return True
        else:
            return False
        
    def get_user_role_by_username(self, table_name: str, username: str):
        """
        Gets user role by his username

        :param table_name: name of table you want to find from
        :param username: username of user

        Returns -1 if user not exists. If exists returns his role.
        """
        try:
            self.cursor.execute(self.queries["get_user_role_by_username"].replace("table_name", table_name), (username,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully got user role by email in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Getting user role by username in {table_name} failed! Full error: {e}")

        role = self.cursor.fetchone()
        
        if role:
            return role
        else:
            return -1

    def drop_temp_profile_by_email(self, table_name: str, email: str):
        """
        Drops temp profile by email

        :param table_name: name of table you want to delete from
        :param email: email of user
        """
        try:
            self.cursor.execute(self.queries["drop_temp_profile_by_email"].replace("table_name", table_name), (email,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully dropped temp user by email in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Dropping for temp user by email in {table_name} failed! Full error: {e}")


    def insert_new_temp_profile(self, table_name: str, username: str, code: str, datetime: str, email: str, name: str, surname: str, grade: int, faculty: str, password: str):
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
        try:
            self.drop_temp_profile_by_email(table_name, email)
            self.cursor.execute(self.queries["insert_new_temp_profile"].replace("table_name", table_name), (email, code, datetime, name, surname, grade, faculty, username,password,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully inserted a temp user in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Inserting user by username and password in {table_name} failed! Full error: {e}")

    def get_temp_profile_by_email(self, table_name: str, email: str):
        """
        Gets temp profile by email

        :param table_name: name of table you want to select
        :param email: email of user
        
        Returns -1 if exception
        Returns all temp user information by email
        """
        try:
            self.cursor.execute(self.queries["get_temp_profile_by_email"].replace("table_name", table_name), (email,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully looked for temp user by email in {table_name}")
            return self.cursor.fetchone()
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Looking for temp user by email in {table_name} failed! Full error: {e}")
            return -1
        

    def create_new_user(self, table_name: str, username: str, name: str, surname: str, email: str, password: str, grade: str, faculty: str):
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
        """
        try:
            self.cursor.execute(self.queries["create_new_user"].replace("table_name", table_name), (username, name, surname, email, password, grade, faculty, DEFAULT_AVATAR,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully added user in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Adding user in {table_name} failed! Full error: {e}")
    
    def get_user_by_username(self, table_name: str, username: str):
        """
        Finds all user infomation by his username
        
        :param table_name: name of table you want to select
        :param username: username of user

        Returns dict with this user information: 
        Username, Name, Surname, Email, Password, Rating, Role, Grade, Faculty, Avatar
        """

        try:
            self.cursor.execute(self.queries["get_user_by_username"].replace("table_name", table_name), (username,))
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
                    "avatar": user_info[9]
                }

                mariadb_logger.log("info", f"[{os.getpid()}] Succesfully got user in {table_name}")

                return mapped_user_info
            else:
                return -1
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Getting user from {table_name} failed! Full error: {e}")

    def update_profile(self, table_name: str, username: str, name: str, surname: str, email: str, grade: int, faculty: str, avatar: str, old_username: str):
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
        """           # """UPDATE table_name SET username = ?, name = ?, surname = ?, email = ?, grade = ?, faculty = ?, avatar = ? WHERE username = ?;"""
        try:
            self.cursor.execute(self.queries["update_profile"].replace("table_name", table_name), (username, name, surname, email, grade, faculty, avatar, old_username,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully updated user in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Updating user in {table_name} failed! Full error: {e}")


    def admin_update_profile(self, table_name: str, username: str, name: str, surname: str, email: str, grade: int, faculty: str, avatar: str, rating: float, role: str, old_username: str):
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
        """           # """UPDATE table_name SET username = ?, name = ?, surname = ?, email = ?, grade = ?, faculty = ?, avatar = ? WHERE username = ?;"""
        try:
            self.cursor.execute(self.queries["admin_update_profile"].replace("table_name", table_name), (username, name, surname, email, grade, faculty, avatar, rating, role, old_username,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully updated user in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Updating user in {table_name} failed! Full error: {e}")
        
    def get_all_users(self, table_name: str):
        """
        Return all users from table
        
        :param table_name: name of table you want to select 
        """
        try:
            self.cursor.execute(self.queries["get_all_users"].replace("table_name", table_name))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully selected all from {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Selecting all from {table_name} failed! Full error: {e}")

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

            info.append(temp_dict)
        
        return info
    
    def get_user_name_surname(self, table_name: str, username: str):
        """
        Updates updatable fields

        :param table_name: name of table you want to select
        :param username: username of user
        """
        try:
            self.cursor.execute(self.queries["get_user_name_surname"].replace("table_name", table_name), (username,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully selected name surname from {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Selecting name surname from {table_name} failed! Full error: {e}")

        info = self.cursor.fetchone()
        if info:
            return info
        else:
            return -1 

    def create_event(self, table_name: str, type: str, title: str, datetime: str, content: str, image: str):
        """
        Creates new event

        :param table_name: name of table you want to select
        :param type: type of event
        :param title: title of event
        :param datetime: datetime of event
        :param content: content of event
        :param image: image of event
        """
        try:
            self.cursor.execute(self.queries["create_event"].replace("table_name", table_name), (type, title, datetime, content, image,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully created event in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Creating event in {table_name} failed! Full error: {e}")

        
    def get_all_events(self, table_name: str):
        """
        Return all events from table
        
        :param table_name: name of table you want to select 
        """
        try:
            self.cursor.execute(self.queries["get_all_events"].replace("table_name", table_name))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully selected all from {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Selecting all from {table_name} failed! Full error: {e}")

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

            info.append(temp_dict)
        
        return info 
    
    def delete_event_by_title(self, table_name: str, title: str):
        """
        Deletes event by title

        :param table_name: name of table you want to delete from
        :param title: title of event
        """
        try:
            self.cursor.execute(self.queries["delete_event_by_title"].replace("table_name", table_name), (title,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully deleted event by title from {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Deleting event by title from {table_name} failed! Full error: {e}")
        
    def get_event_by_title(self, table_name: str, title: str):
        """
        Gets event info by title

        :param table_name: name of table you want to delete from
        :param title: title of event
        """
        try:
            self.cursor.execute(self.queries["get_event_by_title"].replace("table_name", table_name), (title,))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully got event info by title from {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Getting event info by title from {table_name} failed! Full error: {e}")
        
        raw_info = self.cursor.fetchone()

        if raw_info:

            info = {}
            info["type"] = raw_info[0]
            info["title"] = raw_info[1]
            info["datetime"] = raw_info[2]
            info["content"] = raw_info[3]
            info["image"] = raw_info[4]
            info["participants"] = raw_info[5]

            return info 
        else:
            return -1

    def update_event(self, table_name: str, event_type: str, title: str, datetime: str, content: str, image: str, participants: int, old_title: str):
        """
        Updates updatable fields

        :param table_name: name of table you want to insert
        :param title: title of event
        :param datetime: datetime of event
        :param content: content of event
        :param image: path to image of event
        :param participants: participants of event
        :param old_title: old_title of event
        """           # "UPDATE table_name SET type = ?, title = ?, datetime = ?, content = ?, image = ?, participants = ? WHERE title = ?;"
        try:
            self.cursor.execute(self.queries["update_event"].replace("table_name", table_name), (event_type, title, datetime, content, image, participants, old_title))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully updated event in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Updating event in {table_name} failed! Full error: {e}")
    
class User(UserMixin):
    def __init__(self, username, role):
        self.id = username
        self.role = role