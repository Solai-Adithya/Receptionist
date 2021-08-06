from dns.rdatatype import NULL
from dns.resolver import query
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

    # Fetch user using id
    @staticmethod
    def getUserByEmail(email, projection=None):
        userDetails = UsersCollection.find_one({"email": email}, projection)
        if not userDetails:
            return None
        return userDetails

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
        print("Room Details:", room)
        return dict(room)

    # Fetch all rooms created by a user
    @staticmethod
    def getRoomsByCreator(email, projection=None):
        rooms = RoomsCollection.find(
            {"creator": email},
            sort=[("start_date", pymongo.ASCENDING)],
            projection=projection,
        )
        return list(rooms)

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
    def getInvitedParticipantsInRoom(room_id):
        invited_participants = ParticipantsCollection.aggregate(
            [
                {"$match": {"roomID": room_id, "queuePosition":-1}},
                {
                    "$lookup": {
                        "from": "Users",
                        "localField": "email",
                        "foreignField": "email",
                        "as": "user",
                    }
                },
                {"$unwind": "$user"},
                {
                    "$project": {
                        "_id": 0,
                        "user.email": "$user.email",
                        "user.name": "$user.name",
                        "user.profile_pic": "$user.profile_pic",
                    }
                },
                {"$sort": {"queuePosition": pymongo.ASCENDING}},
            ]
        )
        #Additionally sort by invite timestamp later
        return list(invited_participants)

    @staticmethod
    def getUnInvitedParticipantsInRoom(room_id):
        uninvited_participants = ParticipantsCollection.aggregate(
            [
                {"$match": {"roomID": room_id, "queuePosition":{'$gt': 0}}},
                {
                    "$lookup": {
                        "from": "Users",
                        "localField": "email",
                        "foreignField": "email",
                        "as": "user",
                    }
                },
                {"$unwind": "$user"},
                {
                    "$project": {
                        "_id": 0,
                        "queuePosition": 1,
                        "user.email": "$user.email",
                        "user.name": "$user.name",
                        "user.profile_pic": "$user.profile_pic",
                    }
                },
                {"$sort": {"queuePosition": pymongo.ASCENDING}},
            ]
        )
        return list(uninvited_participants)

    @staticmethod
    def getAllParticipantsInRoom(room_id):
        participants = ParticipantsCollection.aggregate(
            [
                {"$match": {"roomID": room_id}},
                {
                    "$lookup": {
                        "from": "Users",
                        "localField": "email",
                        "foreignField": "email",
                        "as": "user",
                    }
                },
                {"$unwind": "$user"},
                {
                    "$project": {
                        "_id": 0,
                        "queuePosition": 1,
                        "user.email": "$user.email",
                        "user.name": "$user.name",
                        "user.profile_pic": "$user.profile_pic",
                    }
                },
                {"$sort": {"queuePosition": pymongo.ASCENDING}},
            ]
        )
        return list(participants)

    @staticmethod
    def getParticipantsEmailsByRoom(room_id):
        #Find list of participants in a room
        participants = ParticipantsCollection.find({"roomID": room_id}, {"_id":0, "email":1})
        result = []
        for participant in participants:
            result.append(participant["email"])
        return result

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

    @staticmethod
    def removeParticipantFromQueue(room_id, email):
        present_queue_position = ParticipantsCollection.find(
            {"roomID": room_id, "email": email}, {"queuePosition": 1}   
        )[0]["queuePosition"]

        if(present_queue_position!=-1):
            ParticipantsCollection.update_many(
                {"roomID":room_id, "queuePosition":{"$gt":present_queue_position}}, {"$inc": {"queuePosition":-1}}
            )
            ParticipantsCollection.update_one(
                {"roomID": room_id, "email": email}, {"$set": {"queuePosition":-1}}
            )
            return True
        else:
            return False

    @staticmethod
    def addInviteTimestamp(room_id, email):
        ParticipantsCollection.update_one(
            {"roomID": room_id, "email": email}, {"$set": {"inviteTimeStamp": datetime.utcnow()}}
        )
        return True

    @staticmethod
    def reorderParticipants(room_id, email, new_position):
        present_queue_position = ParticipantsCollection.find(
            {"roomID": room_id, "email": email}, {"queuePosition": 1}   
        )[0]["queuePosition"]
        if(present_queue_position!=-1):
            ParticipantsCollection.update_many(
                {"roomID":room_id, "queuePosition":{"$gt":present_queue_position}}, {"$inc": {"queuePosition":-1}}
            )
            ParticipantsCollection.update_many(
                {"roomID":room_id, "queuePosition":{"$gte":new_position}}, {"$inc": {"queuePosition":1}}
            )
            ParticipantsCollection.update_one(
                {"roomID": room_id, "email": email}, {"$set": {"queuePosition":new_position}}
            )
            return True
        else:
            return False