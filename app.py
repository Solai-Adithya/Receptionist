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


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/manage", methods=["POST"])
def getFromDB():
    queryOutput = db.Rooms.find({})
    return dumps(queryOutput)

# @app.route("/")
# def queue():
#     return render_template("home.html", course = courses_list)


if __name__ == "__main__":
    socketio.run(app)
