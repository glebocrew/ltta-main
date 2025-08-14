from flask import Flask

# imports

app = Flask(__name__)

# flask app conf

@app.route("/")
def hello():
    return "<h >Hello!<h1>"

# routes

if __name__ == "__main__":
    app.run(host='0.0.0.0')
 
# start point