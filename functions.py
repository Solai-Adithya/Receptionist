import random
def generateRoomID():
    roomID = ""
    for i in range(4):
        roomID += chr(random.randint(97,122))
    return roomID