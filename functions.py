import random
import functools
from flask_login import current_user
from flask_socketio import disconnect


def generateRoomID():
    roomID = "".join([chr(random.randint(97, 122)) for _ in range(5)])
    return roomID


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)

    return wrapped
