from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import pymongo
import requests
from constants import adhiAtlasAdminPassword
from bson.json_util import dumps
from bson.objectid import ObjectId
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
Users = db.Users
Rooms = db.Rooms


@app.route("/")
def home():
    return render_template("home.html")


@app.route('/findRoom/<roomId>/', methods=['GET'])
def findRoom(roomId):
    queryObject = {"_id": ObjectId(str(roomId))}
    query = Rooms.find_one(queryObject)
    query.pop('_id')
    return dumps(query)


@app.route('/findUser/<userId>/', methods=['GET'])
def findUser(userId):
    queryObject = {"_id": ObjectId(str(userId))}
    query = Users.find_one(queryObject)
    query.pop('_id')
    return dumps(query)


# @app.route("/")
# def queue():
#     return render_template("home.html", course = courses_list)


if __name__ == "__main__":
    socketio.run(app)
