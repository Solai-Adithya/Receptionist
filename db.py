from flask.helpers import get_root_path
import pymongo
from flask_login import UserMixin
from bson.json_util import dumps
from bson.objectid import ObjectId
from constants import ATLAS_ADMIN_PWD
from functions import generateRoomID
# from db import get_db

connectionURL = (
    "mongodb+srv://adhiAtlasAdmin:%s@cluster0.cjyig.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    % ATLAS_ADMIN_PWD
)
dbclient = pymongo.MongoClient(connectionURL)
db = dbclient.get_database("Reception")
UsersCollection = db.Users
RoomsCollection = db.Rooms
ParticipantsCollection = db.Participants

class User(UserMixin):
    def __init__(self, id_, name, first_name, email, profile_pic):
        self.id = id_
        self.name = name
        self.first_name = first_name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        user = UsersCollection.find_one({"userID": user_id})
        if not user:
            return None
        user = User(user["_id"], user["name"], user["first_name"], user["email"], user["profile_pic"])
        return user

    @staticmethod
    def create(id_, name, first_name, email, profile_pic):
        UsersCollection.insert_one(
            {
                "userID": id_,
                "name": name,
                "first_name": first_name,
                "email": email,
                "profile_pic": profile_pic,
            }
        )

class Rooms:
    @staticmethod
    def getRoomByID(room_id):
        room = RoomsCollection.find_one({"_id": room_id})
        if not room:
            return None
        print(room)
        return room
    
    @staticmethod
    def getRoomsByCreator(email):
        rooms = RoomsCollection.find({"email": email})
        if not rooms:
            return None
        print(rooms) # should be list of rooms, not checked for errors
        return rooms    
    
    @staticmethod
    def getRoomsByParticipant(email):
        rooms = RoomsCollection.find({"email": email})
        if not rooms:
            return None
        print(rooms) # should be list of rooms, not checked for errors
        return rooms

    @staticmethod
    def createRoom(roomDetails):
        RoomsCollection.insert_one(roomDetails)

class Participants:
    @staticmethod
    def getParticipantsByRoom(room_id):
        participants = ParticipantsCollection.find({"roomID": room_id})
        if not participants:
            return None
        print(participants) # should be list of participants, not checked for errors
        return participants

    @staticmethod
    def addParticipants(room_id, emails):
        documents = []
        queuePosition = 100
        for email in emails:
            documents.append({
                "roomID": room_id, 
                "email": email,
                "status": "open",
                "windowLowerBound": None,
                "windowUpperBound": None,
                "queuePosition": queuePosition,
                "notifiedByWebsite": False,
                "notifiedByEmail": False
            })
            queuePosition += 100
        ParticipantsCollection.insert_many(documents)
