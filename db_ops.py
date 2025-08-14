from mariadb import Connection, Cursor
from utils.logger import Logger
import os

# imports

mariadb_logger = Logger("logs.txt", __file__)

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
            mariadb_logger.log("info", f"Connecting to mariadb with arguments {connection_conf}.")
            self.mariaconnection = Connection(**self.conf)
            self.mariaconnection.autocommit = True

            mariadb_logger.log("info", f"Successfully connected to mariadb.")
        except Exception as e:
            mariadb_logger.log("error", f"Connection to mariadb was not established: arguments are not correct. Full exception: {e}")
            mariadb_logger.log("fatal", f"MariaDB module (.py) was stopped. Read logs upper.")
            os.exit(1)
        
        self.cursor = Cursor(self.mariaconnection)
        self.queries = {
            "select_all": "SELECT * FROM table_name;" 
        }

    def select_all(self, table_name):
        """
        Selecting all from some table
        :param table_name: name of table you want to select
        """
        mariadb_logger.log("info", f"Selecting all from {table_name}")
        try:
            self.cursor.execute(self.queries["select_all"].replace("table_name", table_name))
            mariadb_logger.log("info", f"Succesfully selected all from {table_name}")
        except Exception as e:
            mariadb_logger.log("error", f"Selecting all from {table_name} failed! Full error: {e}")

        return self.cursor.fetchall()
            