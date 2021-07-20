import pymongo
from flask_login import UserMixin
from bson.json_util import dumps
from bson.objectid import ObjectId
from constants import ATLAS_ADMIN_PWD

# from db import get_db

connectionURL = (
    "mongodb+srv://adhiAtlasAdmin:%s@cluster0.cjyig.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    % ATLAS_ADMIN_PWD
)
dbclient = pymongo.MongoClient(connectionURL)
db = dbclient.get_database("Reception")
UsersCollection = db.Users

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        user = UsersCollection.find_one({"userID": user_id})
        if not user:
            return None
        user = User(user["_id"], user["name"], user["email"], user["profile_pic"])
        return user

    @staticmethod
    def create(id_, name, email, profile_pic):
        UsersCollection.insert_one(
            {
                "userID": id_,
                "name": name,
                "email": email,
                "profile_pic": profile_pic,
            }
        )