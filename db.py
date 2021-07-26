import pymongo
from flask_login import UserMixin
from bson.json_util import dumps
from constants import ATLAS_ADMIN_PWD

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

    #Fetch user using id
    @staticmethod
    def get(user_id):
        user = UsersCollection.find_one({"userID": user_id})
        if not user:
            return None
        user = User(
            user["_id"],
            user["name"],
            user["first_name"],
            user["email"],
            user["profile_pic"],
        )
        return user

    #Create a new user
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
    #Fetch room details using room ID
    @staticmethod
    def getRoomByID(room_id):
        room = RoomsCollection.find_one({"_id": room_id})
        if not room:
            return None
        return dict(room)

    #Fetch all rooms created by a user
    @staticmethod
    def getRoomsByCreator(email):
        rooms = RoomsCollection.find({"creator": email})
        if not rooms:
            return None
        return list(rooms)

    #Create a new room
    @staticmethod
    def createRoom(roomDetails):
        RoomsCollection.insert_one(roomDetails)


class Participants:
    #List of rooms where the user is a participant
    #TODO: Add a method to fetch rooms where user is a participant after the present date
    @staticmethod
    def getRoomsByParticipant(email):
        rooms = ParticipantsCollection.find({"email": email})
        if not rooms:
            return None
        rooms = list(rooms)
        for i in range(len(rooms)):
            room = rooms[i]
            roomDetails = Rooms.getRoomByID(room["roomID"])
            if(roomDetails == None): #Room ID is present in the participants collection but not in the rooms collection
                return "Database Mismatch"
            rooms[i].update(roomDetails)
        rooms = sorted(rooms, key=lambda k: k["startTime"])
        return rooms

    #List of participants in a room
    @staticmethod
    def getParticipantsByRoom(room_id):
        participants = ParticipantsCollection.find({"roomID": room_id})
        if not participants:
            return None
        participants = list(participants)
        participants = sorted(participants, key=lambda k: k["queuePosition"])
        return participants

    #Add participants to a room
    @staticmethod
    def addParticipants(room_id, emails):
        documents = []
        queuePosition = 100
        for email in emails:
            documents.append(
                {
                    "roomID": room_id,
                    "email": email,
                    "status": "open",
                    "windowLowerBound": None,
                    "windowUpperBound": None,
                    "queuePosition": queuePosition,
                    "notifiedByWebsite": False,
                    "notifiedByEmail": False,
                }
            )
            queuePosition += 100
        ParticipantsCollection.insert_many(documents)
