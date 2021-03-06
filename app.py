import json
import os
from csv import reader
from datetime import datetime
from io import StringIO

import requests
from curtsies.fmtfuncs import blue, bold, green, red, yellow
from flask import Flask
from flask import abort as flask_abort
from flask import jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_socketio import SocketIO, emit, join_room
from oauthlib.oauth2 import WebApplicationClient

from constants import GOOGLE_CLIENT_ID, GOOGLE_DISCOVERY_URL, GOOGLE_SECRET
from db import Participants, ParticipantsCollection, Rooms, User
from functions import generateRoomID, invite_user, notify_user

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["FLASK_ENV"] = "development"

rooms = Rooms()
participants = Participants()

app = Flask(__name__)

app.config["SECRET_KEY"] = "secret!"
app.debug = False

socketio = SocketIO(
    app, async_mode="eventlet", logger=True, engineio_logger=False
)

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


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/manage/<roomID>/")
@login_required
def manage(roomID):
    """
    Allowed only if user created the room.
    """
    roomDetail = rooms.getRoomByID(roomID, projection=["creator"])
    if roomDetail is not None and roomDetail["creator"] == current_user.email:
        invitedPariticipants = participants.getInvitedParticipantsInRoom(
            roomID
        )
        uninvitedParticipants = participants.getUnInvitedParticipantsInRoom(
            roomID
        )
        emit(
            "to-join",
            {"data": current_user.email, "roomID": roomID},
            to=roomID,
            namespace="/",
        )
        return render_template(
            "manage.html",
            roomID=roomID,
            invitedParticipants=invitedPariticipants,
            uninvitedParticipants=uninvitedParticipants,
        )
    else:
        flask_abort(403)


@app.route("/get_QP", methods=["POST"])
def getQueuePosition():
    data = request.get_json(force=True)
    roomID = data["roomID"]
    res = Participants.getQueuePosition(roomID, current_user.email)
    print(bold(green(f"{roomID}, {current_user.email}, {res}")))
    return res


@app.route("/invite", methods=["POST"])
def invite():
    js = request.get_json(force=True)
    room_id = js["roomID"]
    participant_email = js["email"]

    print(bold(blue(f"Inviting {participant_email = } to {room_id = }")))
    if (
        participants.ifParticipantInRoom(room_id, participant_email)
        is not None
    ):
        invite_user(room_id, participant_email)
        # notify the next participant to be
        # ready by email and website if online - experimental
        print(bold(blue(f"Successful , {room_id=}, {participant_email=}")))
        participants.removeParticipantFromQueue(room_id, participant_email)
        participants.addInviteTimestamp(room_id, participant_email)
        return {"result": "success"}
    else:
        return {"result": "failure"}


@app.route("/notify", methods=["POST"])
def notify():
    js = request.get_json(force=True)
    room_id = js["roomID"]
    participant_email = js["email"]
    if (
        participants.ifParticipantInRoom(room_id, participant_email)
        is not None
    ):
        invite_user(room_id, participant_email)
        res = {"result": "success"}
    else:
        res = {"result": "failure"}
    return jsonify(res)


@app.route("/join/<roomID>/")
@login_required
def flask_join_room(roomID):
    """
    Allowed only if user is a participant.
    """
    if (
        participants.ifParticipantInRoom(roomID, current_user.email)
        is not None
    ):
        emit(
            "to-join",
            {"data": current_user.email, "roomID": roomID},
            to=roomID,
            namespace="/",
        )
        joiningDetails = participants.getJoiningDetails(
            roomID, current_user.email
        )
        return render_template("participant.html", **joiningDetails)
    else:
        flask_abort(403)


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


@socketio.on("to-join")
def io_to_join_room(data):
    print(bold(yellow(f"{data['data']} to join {data['roomID']}")))
    socketio.join_room(data.roomID)


@socketio.on("connect")
def io_join_room(data=None):
    print(bold(yellow(f"{current_user.email} joined {data}")))


@socketio.on("disconnect")
def on_leave(data=None):
    """
    Sent after leaving a room.
    """
    print(bold(yellow(f"{current_user.email} left {data}")))


if __name__ == "__main__":
    socketio.run(
        app, host="localhost", port=5000, log_output=True, use_reloader=True
    )
