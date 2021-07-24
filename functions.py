import random


def generateRoomID():
    roomID = "".join([chr(random.randint(97, 122)) for _ in range(16)])
    return roomID
