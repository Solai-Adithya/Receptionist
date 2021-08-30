import json
import os
import requests
from curtsies.fmtfuncs import bold, yellow

from flask import Flask, redirect, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_socketio import SocketIO, join_room
from oauthlib.oauth2 import WebApplicationClient

import views
from constants import GOOGLE_CLIENT_ID, GOOGLE_SECRET
from db import User
from functions import get_google_provider_cfg

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["FLASK_ENV"] = "development"


def make_app(name):
    app = Flask(name)
    app.config["SECRET_KEY"] = "secret!"
    app.debug = False
    return app


app = make_app(__name__)

app.add_url_rule("/", view_func=views.home)
app.add_url_rule("/create/<method>", view_func=views.createRoom)
app.add_url_rule(
    "/attendees/<method>", view_func=views.attendees_add, methods=["POST"]
)
app.add_url_rule("/manage/<roomID>/", view_func=views.manage)
app.add_url_rule("/get_QP", view_func=views.getQueuePosition, methods=["POST"])
app.add_url_rule("/invite", view_func=views.invite, methods=["POST"])
app.add_url_rule("/notify", view_func=views.notify, methods=["POST"])
app.add_url_rule("/join/<roomID>/", view_func=views.flask_join_room)

client = WebApplicationClient(GOOGLE_CLIENT_ID)
login_manager = LoginManager()
login_manager.init_app(app)

socketio = SocketIO(
    app,
    message_queue="redis://",
    async_mode="threading",
    logger=True,
    engineio_logger=False,
    cors_allowed_origins="*",
)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


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


@socketio.on("message")
def handle_message(event, data):
    socketio.emit("ping", data)
    # socketio.emit("updated room", to="acbqulalolxrnvyw")
    print("received message: " + event, data)


@socketio.on("to-join")
def io_to_join_room(data):
    join_room(data["roomID"])
