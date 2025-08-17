from mariadb import Connection, Cursor
from utils.logger import Logger
from flask_login import UserMixin
import sys, os

# imports

mariadb_logger = Logger("logs/mariadb.txt", __file__)

# logger

DEFAULT_AVATAR = open("static/img/user.png", "rb").read()

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
            "create_new_user": "INSERT INTO users (username, name, surname, email, password, rating, role, grade, faculty, avatar) VALUES (?, ?, ?, ?, ?, 0, 'user', ?, ?, ?);"
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

    def drop_temp_profile_by_email(self, table_name: str, email: str):
        """
        Drops temp profile by email

        :param table_name: name of table you want to select
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

        :param table_name: name of table you want to select
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
        :param username: username of user
        :param name: name of user
        :param surname: surname of user
        :param email: email of user
        :param password: password of user
        :param grade: email of user
        :param faculty:  email of user
        """
        try:
            self.cursor.execute(self.queries["create_new_user"].replace("table_name", table_name), (username, name, surname, email, password, grade, faculty, DEFAULT_AVATAR))
            mariadb_logger.log("info", f"[{os.getpid()}] Succesfully added user in {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"[{os.getpid()}] Adding user in {table_name} failed! Full error: {e}")
        
        

class User(UserMixin):
    def __init__(self, username):
        self.id = username