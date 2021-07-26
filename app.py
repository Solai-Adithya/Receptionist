import json
import os
from csv import reader
from datetime import datetime
from io import StringIO
from pprint import pprint

import requests
from flask import Flask
from flask import abort as flask_abort
from flask import redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from oauthlib.oauth2 import WebApplicationClient

from constants import GOOGLE_CLIENT_ID, GOOGLE_DISCOVERY_URL, GOOGLE_SECRET
from db import Participants, Rooms, User
from functions import authenticated_only, generateRoomID

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["FLASK_ENV"] = "development"

rooms = Rooms()
participants = Participants()

app = Flask(__name__)

app.config["SECRET_KEY"] = "secret!"
app.debug = False

socketio = SocketIO(app, logger=True, engineio_logger=True)

client = WebApplicationClient(GOOGLE_CLIENT_ID)
login_manager = LoginManager()
login_manager.init_app(app)

# Login
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


# Homepage
@app.route("/")
def home():
    if current_user.is_authenticated:
        createdRooms = rooms.getRoomsByCreator(current_user.email)
        RoomsbyParticipation = participants.getRoomsByParticipant(
            current_user.email
        )
        return render_template(
            "upcoming.html",
            createRoomsTable=createdRooms,
            RoomsbyParticipationTable=RoomsbyParticipation,
            user_name=current_user.name,
            user_email=current_user.email,
            user_profile_pic=current_user.profile_pic,
        )
    else:
        return render_template("homePageNotLoggedIn.html")


@app.route("/create/<method>")
@login_required
def createRoom(method):
    if method in ("add", "invite"):
        return render_template(
            "newroom.html", add=(method == "add"), method=method
        )
    else:
        flask_abort(404)


@app.route("/attendees/<method>", methods=["POST"])
@login_required
def attendees_add(method):

    startDate = datetime.strptime(request.form["start-date"], r"%Y-%m-%d")
    startTime = datetime.strptime(request.form["start-time"], r"%H:%M")
    start_datetime = datetime.combine(startDate.date(), startTime.time())

    name = request.form["name"]
    link = request.form["meet-link"]
    description = request.form["description"]
    room_id = None

    roomDetails = {
        "_id": room_id,
        "start_date": start_datetime,
        "name": name,
        "description": description,
        "meeting_link": link,
        "creator": current_user.email,
    }

    if method == "add":

        room_id = generateRoomID()
        while rooms.getRoomByID(room_id) is not None:
            room_id = generateRoomID()
        roomDetails["_id"] = room_id

        emails = request.files["uploadEmails"].read().decode()

        with StringIO(emails) as input_file:
            csv_reader = reader(input_file, delimiter="\n")
            emails = [row[0] for row in csv_reader]

        rooms.createRoom(roomDetails)
        participants.addParticipants(room_id, emails)
        return redirect(url_for("manage", roomID=room_id))

    elif method == "invite":

        room_id = request.form["room-id"]
        roomDetails["_id"] = room_id

        if rooms.getRoomByID(room_id) is None:
            rooms.createRoom(roomDetails)
            return redirect(url_for("manage", roomID=room_id))
        else:
            return (
                "Sorry!, that room code is already taken, please refill data"
            )
            # Replace with HTML page with the form details present and just error saying room code already exists
            # Potential:
            # Maybe use "flash" ?
            # Or check the roomId while typing using AjaX ?


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/manage/<roomID>/")
@login_required
def manage(roomID):
    participantsofRoom = participants.getParticipantsByRoom(roomID)
    RoomsbyParticipation = participants.getRoomsByParticipant(
        "b19268@students.iitmandi.ac.in"  # DEBUG
    )
    return render_template("manage.html", roomID=roomID)


# Login
@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )

    return redirect(request_uri)


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
    userinfo_data = userinfo_response.json()
    if userinfo_data.get("email_verified") is not None:
        unique_id = userinfo_data["sub"]
        users_email = userinfo_data["email"]
        picture = userinfo_data["picture"]
        name = userinfo_data["name"]
        first_name = userinfo_data["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    user = User(
        id_=unique_id,
        name=name,
        first_name=first_name,
        email=users_email,
        profile_pic=picture,
    )
    if not User.get(unique_id):
        User.create(unique_id, name, first_name, users_email, picture)
    login_user(user)

    return redirect("/")


# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@socketio.on("join")
@authenticated_only
def on_join(data):
    username = data["username"]
    room = data["room"]
    join_room(room)
    send(username + " has entered the room.", to=room)


@socketio.on("leave")
def on_leave(data):
    username = data["username"]
    room = data["room"]
    leave_room(room)
    send(username + " has left the room.", to=room)


@socketio.on("connect")
def test_connect(auth):
    emit("my response", {"data": "Connected"})


@socketio.on("disconnect")
def test_disconnect():
    print("Client disconnected")


if __name__ == "__main__":
    socketio.run(
        app, host="localhost", port=5000, log_output=True, use_reloader=True
    )
