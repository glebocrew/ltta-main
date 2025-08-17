from mariadb import Connection, Cursor
from utils.logger import Logger
from flask_login import UserMixin
import sys, os

# imports

mariadb_logger = Logger("logs/mariadb.txt", __file__)

# logger

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
            "find_user_by_login_and_password": "SELECT * FROM table_name WHERE username = ? AND password = ?;"
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
            mariadb_logger.log("error", f"[{os.getpid()}] Finding user by username and password in {table_name} failed! Full error: {e}")
        
        
        if self.cursor.fetchone():
            return True
        else:
            return False


    def insert_new_code(self, table_name: str, username: str, code: str, datetime: str):
        """
        Inserts new verification code

        :param table_name: name of table you want to select
        :param username: username of user
        :param code: code of user
        :param datetime: code of user
        """

class User(UserMixin):
    def __init__(self, username):
        self.id = username