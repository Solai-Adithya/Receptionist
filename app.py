from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import pymongo
import requests
from constants import adhiAtlasAdminPassword
from bson.json_util import dumps
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

if __name__ == '__main__':
    socketio.run(app)

connectionURL = "mongodb+srv://adhiAtlasAdmin:%s@cluster0.cjyig.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"%adhiAtlasAdminPassword
client = pymongo.MongoClient(connectionURL)
db = client.get_database('Reception')

# print("Working till here")\

@app.route('/manage', methods=['POST'])
def getFromDB():
    queryOutput = db.Rooms.find({})
    return dumps(queryOutput)







