import smtplib
import random
import requests
from constants import EMAIL_ID, EMAIL_PASSWORD, GOOGLE_DISCOVERY_URL
from email.message import EmailMessage
from db import User, Rooms


def generateRoomID():
    roomID = "".join([chr(random.randint(97, 122)) for _ in range(16)])
    return roomID


# Login
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def invite_user(room_id, participant_email):
    # Ask user to join the room immediately
    room = Rooms.getRoomByID(room_id)
    room_name = room["name"]
    interviewer_email = room["creator"]
    meet_link = room["meeting_link"]
    interviewer_name = User.getUserByEmail(interviewer_email, {"name": 1})[
        "name"
    ]
    msg = EmailMessage()
    msg["Subject"] = (
        "%s invited you to join the meeting. Join Now!" % interviewer_name
    )
    msg["From"] = EMAIL_ID
    msg["To"] = participant_email

    msg.set_content(
        f"""
    {interviewer_name} invited you to join the {room_name} meeting using the below link right now. Please join as soon as possible.
    Meeting Link: {meet_link}

    On behalf of {interviewer_name} ({interviewer_email}),
    Receptionist.tech
    """
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ID, EMAIL_PASSWORD)
        smtp.send_message(msg)


def notify_user(room_id, participant_email):
    # Alert user to be ready to join the room next. Experimental feature.
    room = Rooms.getRoomByID(room_id)
    room_name = room["name"]
    interviewer_email = room["creator"]
    meet_link = room["meeting_link"]
    interviewer_name = User.getUserByEmail(interviewer_email, {"name": 1})[
        "name"
    ]
    msg = EmailMessage()
    msg["Subject"] = "You are up next. Get ready!"
    msg["From"] = EMAIL_ID
    msg["To"] = participant_email

    msg.set_content(
        f"""
    You are the next person in {room_name}'s participant queue. You can find the meeting link below. Get ready! 
    Meeting Link: {meet_link}

    Further you will be notified when {interviewer_name} invites you to join the meeting.

    On behalf of {interviewer_name} ({interviewer_email}),
    Receptionist.tech
    """
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ID, EMAIL_PASSWORD)
        smtp.send_message(msg)
