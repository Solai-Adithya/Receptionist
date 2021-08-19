import main
from db import ParticipantsCollection
from curtsies.fmtfuncs import bold, green, bold, red

print(bold(red("Listening...")))
with ParticipantsCollection.watch(full_document="updateLookup") as stream:
    for change in stream:
        doc = change["fullDocument"]
        print(doc)
        main.socketio.emit("updated room", to=doc["roomID"])
        print(bold(green(f"updated | roomid = {doc['roomID']}")))
