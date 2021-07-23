import json
import os
import secrets
from csv import reader
from datetime import datetime
from io import StringIO

import pymongo
import requests
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_socketio import SocketIO
from oauthlib.oauth2 import WebApplicationClient

from constants import (
    ATLAS_ADMIN_PWD,
    GOOGLE_CLIENT_ID,
    GOOGLE_DISCOVERY_URL,
    GOOGLE_SECRET,
)
from user import User

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["FLASK_ENVIRONMENT"] = "development"

app = Flask(__name__)

app.config["SECRET_KEY"] = "secret!"
app.debug = True

socketio = SocketIO(app)

connectionURL = (
    "mongodb+srv://adhiAtlasAdmin:%s@cluster0.cjyig.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    % ATLAS_ADMIN_PWD
)
dbclient = pymongo.MongoClient(connectionURL)
db = dbclient.get_database("Reception")
Users = db.Users
Rooms = db.Rooms

# Login
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


# Homepage
@app.route("/")
def index():
    if current_user.is_authenticated:
        return render_template(
            "index.html",
            user_name=current_user.name,
            user_email=current_user.email,
            user_profile_pic=current_user.profile_pic,
        )
    else:
        return render_template("homePageNotLoggedIn.html")


@app.route("/upcoming")
@login_required
def upcoming():
    return render_template("upcoming.html")  # TODO


@app.route("/create")
def createRoom():
    return render_template("newroom.html")


@app.route("/attendees", methods=["POST"])
def attendees():
    start_time = datetime.strptime(
        request.form["start-time"], r"%Y-%m-%dT%H:%M"
    )
    title = request.form["meet-title"]
    link = request.form["meet-link"]
    emails = request.files["uploadEmails"].read().decode()
    room_id = secrets.token_urlsafe()
    with StringIO(emails) as input_file:
        csv_reader = reader(input_file, delimiter="\n")
        emails = [row[0] for row in csv_reader]
    return str(link)


@app.route("/findRoom/<roomId>/", methods=["GET"])
def findRoom(roomId):
    queryObject = {"_id": ObjectId(str(roomId))}
    query = Rooms.find_one(queryObject)
    query.pop("_id")
    return dumps(query)


@app.route("/findUser/<userId>/", methods=["GET"])
def findUser(userId):
    queryObject = {"_id": ObjectId(str(userId))}
    query = Users.find_one(queryObject)
    query.pop("_id")
    return dumps(query)


client = WebApplicationClient(GOOGLE_CLIENT_ID)
login_manager = LoginManager()
login_manager.init_app(app)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )

    return redirect(request_uri)


# Login Callback
@app.route("/login/callback")
def callback():
    code = request.args.get("code")
    # result = "<p>code: " + code + "</p>"
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_SECRET),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # result = result + "<p>token_response: " + token_response.text + "</p>"
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)
    login_user(user)

    return redirect("/")


# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="localhost", port=5000)

if __name__ == "__main__":
    socketio.run(app)
