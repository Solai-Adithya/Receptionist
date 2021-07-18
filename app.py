from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import pymongo
import requests
from constants import adhiAtlasAdminPassword
from bson.json_util import dumps

app = Flask(__name__, template_folder="./Frontend", static_folder="./static/")

app.config["SECRET_KEY"] = "secret!"
app.debug = True

socketio = SocketIO(app)

connectionURL = (
    "mongodb+srv://adhiAtlasAdmin:%s@cluster0.cjyig.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    % adhiAtlasAdminPassword
)
client = pymongo.MongoClient(connectionURL)
db = client.get_database("Reception")


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/manage", methods=["POST"])
def getFromDB():
    queryOutput = db.Rooms.find({})
    return dumps(queryOutput)

if __name__ == "__main__":
    socketio.run(app)
