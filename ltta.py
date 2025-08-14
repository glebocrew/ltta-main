from flask import Flask, render_template
from utils.logger import Logger
from json import load
from db_ops import MariaConnection
import sys, os
import db_ops

# imports

app = Flask(__name__)
app.secret_key = "dummy_key"
app.template_folder = "templates/"
app.static_folder = "static/"


# flask app conf

logger = Logger("logs/logs.txt", __file__)

# logger conf

try:
    logger.log("info", f"[{os.getpid()}] Loading mariadb configure.")
    json_conf = load(open("conf.json"))
    connection = MariaConnection(json_conf["db"])
    logger.log("info", f"{connection}")
    logger.log("info", f"[{os.getpid()}] Successfully loaded mariadb confs.")
except:
    logger.log("error", f"[{os.getpid()}] There are no database configure file.")
    logger.log("fatal", f"[{os.getpid()}] The main app was stopped since there're no mariadb confs.")
    sys.exit(1)

# mariadb conf

@app.route("/")
def hello():
    return render_template("test.html", flashed_message=f"mariadb table tests now contains: {connection.select_all("test")[0]}")
    

# routes

if __name__ == "__main__":
    app.run(host='0.0.0.0')
 
# start point

logger.stop()