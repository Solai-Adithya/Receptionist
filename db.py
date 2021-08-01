import pymongo
from flask_login import UserMixin
from constants import ATLAS_ADMIN_PWD
from datetime import datetime

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

    # Fetch user using id
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

    # Create a new user
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
    # Fetch room details using room ID
    @staticmethod
    def getRoomByID(room_id, projection=None):
        room = RoomsCollection.find_one(
            {"_id": room_id}, projection=projection
        )
        return room

    # Fetch all rooms created by a user
    @staticmethod
    def getRoomsByCreator(email, projection=None):
        rooms = RoomsCollection.find(
            {"creator": email},
            sort=[("start_date", pymongo.ASCENDING)],
            projection=projection,
        )
        return rooms

    # Create a new room
    @staticmethod
    def createRoom(roomDetails):
        RoomsCollection.insert_one(roomDetails)


class Participants:
    @staticmethod
    def getJoiningDetails(room_id, email):
        roomDetails = dict(RoomsCollection.find_one(
            {"_id": room_id} 
        ))
        print("ROOM details:", roomDetails)
        interviewerDetails = dict(UsersCollection.find_one(
            {"email": roomDetails["creator"]}, {"name":1, "profile_pic":1}
        ))
        participantDetails = dict(ParticipantsCollection.find_one(
            {"email": email}, {"windowLowerBound":1, "windowUpperBound":1, "status":1, "queuePosition":1}
        ))
        participantDetails["interviewer_name"] = interviewerDetails["name"]
        participantDetails["interviewer_profile_pic"] = interviewerDetails["profile_pic"]
        participantDetails.update(roomDetails)
        print(participantDetails)
        return participantDetails
         
    # List of rooms where the user is a participant
    @staticmethod
    def getRoomsByParticipant(email):
        rooms = ParticipantsCollection.aggregate(
            [
                {"$match": {"email": email}},
                {"$project": {"roomID": 1, "_id": 0}},
                {
                    "$lookup": {
                        "from": "Rooms",
                        "localField": "roomID",
                        "foreignField": "_id",
                        "as": "roomID",
                    }
                },
                {"$unwind": {"path": "$roomID"}},
                {
                    "$match": {
                        "roomID.start_date": {
                            "$gte": datetime.utcnow().replace(
                                hour=0, minute=0, second=0
                            )
                        }
                    }
                },
                {
                    "$sort": {
                        "roomID.start_date": pymongo.ASCENDING,
                    }
                },
            ]
        )

        return rooms

    # List of participants in a room
    @staticmethod
    def getParticipantsByRoom(room_id):
        participants = ParticipantsCollection.find(
            {"roomID": room_id},
            sort=[
                ("queuePosition", pymongo.ASCENDING),
            ],
        )
        return participants

    # Add participants to a room
    @staticmethod
    def addParticipants(room_id, emails):
        documents = []
        queuePosition = 1
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
            queuePosition += 1
        ParticipantsCollection.insert_many(documents)

    @staticmethod
    def ifParticipantInRoom(room_id, email):
        return ParticipantsCollection.find_one(
            {"roomID": room_id, "email": email}
        )
