from csv import reader
from datetime import datetime
from io import StringIO

from curtsies.fmtfuncs import blue, bold, green
from flask import abort as flask_abort
from flask import jsonify, redirect, render_template, request, url_for
from flask_login import (
    current_user,
    login_required,
)
from flask_socketio import emit
from db import Participants, Rooms
from functions import generateRoomID, invite_user


def home():
    if current_user.is_authenticated:
        createdRooms = Rooms.getRoomsByCreator(current_user.email)
        RoomsbyParticipation = Participants.getRoomsByParticipant(
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


@login_required
def createRoom(method):
    if method in ("add", "invite"):
        return render_template(
            "newroom.html", add=(method == "add"), method=method
        )
    else:
        flask_abort(404)


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
        while Rooms.getRoomByID(room_id) is not None:
            room_id = generateRoomID()
        roomDetails["_id"] = room_id

        emails = request.files["uploadEmails"].read().decode()

        with StringIO(emails) as input_file:
            csv_reader = reader(input_file, delimiter="\n")
            emails = [row[0] for row in csv_reader]

        Rooms.createRoom(roomDetails)
        Participants.addParticipants(room_id, emails)
        return redirect(url_for("manage", roomID=room_id))

    elif method == "invite":

        room_id = request.form["room-id"]
        roomDetails["_id"] = room_id

        if Rooms.getRoomByID(room_id) is None:
            Rooms.createRoom(roomDetails)
            return redirect(url_for("manage", roomID=room_id))
        else:
            return (
                "Sorry!, that room code is already taken, please refill data"
            )


@login_required
def manage(roomID):
    """
    Allowed only if user created the room.
    """
    roomDetail = Rooms.getRoomByID(roomID, projection=["creator"])
    if roomDetail is not None and roomDetail["creator"] == current_user.email:
        invitedPariticipants = Participants.getInvitedParticipantsInRoom(
            roomID
        )
        uninvitedParticipants = Participants.getUnInvitedParticipantsInRoom(
            roomID
        )
        return render_template(
            "manage.html",
            roomID=roomID,
            invitedParticipants=invitedPariticipants,
            uninvitedParticipants=uninvitedParticipants,
        )
    else:
        flask_abort(403)


def getQueuePosition():
    data = request.get_json(force=True)
    roomID = data["roomID"]
    res = Participants.getQueuePosition(roomID, current_user.email)
    print(bold(green(f"{roomID}, {current_user.email}, {res}")))
    return res


def invite():
    js = request.get_json(force=True)
    room_id = js["roomID"]
    participant_email = js["email"]

    print(bold(blue(f"Inviting {participant_email = } to {room_id = }")))
    if (
        Participants.ifParticipantInRoom(room_id, participant_email)
        is not None
    ):
        invite_user(room_id, participant_email)
        # notify the next participant to be
        # ready by email and website if online - experimental
        print(bold(blue(f"Successful , {room_id=}, {participant_email=}")))
        Participants.removeParticipantFromQueue(room_id, participant_email)
        Participants.addInviteTimestamp(room_id, participant_email)
        return {"result": "success"}
    else:
        return {"result": "failure"}


def notify():
    js = request.get_json(force=True)
    room_id = js["roomID"]
    participant_email = js["email"]
    if (
        Participants.ifParticipantInRoom(room_id, participant_email)
        is not None
    ):
        invite_user(room_id, participant_email)
        res = {"result": "success"}
    else:
        res = {"result": "failure"}
    return jsonify(res)


@login_required
def flask_join_room(roomID):
    """
    Allowed only if user is a participant.
    """
    if (
        Participants.ifParticipantInRoom(roomID, current_user.email)
        is not None
    ):
        joiningDetails = Participants.getJoiningDetails(
            roomID, current_user.email
        )
        return render_template("participant.html", **joiningDetails)
    else:
        flask_abort(403)
