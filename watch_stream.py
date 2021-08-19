from main import socketio
from db import ParticipantsCollection
from curtsies.fmtfuncs import blue, bold, green, bold, red
from pprint import pprint

print(bold(red("Listening...")))
with ParticipantsCollection.watch(full_document="updateLookup") as stream:
    for change in stream:
        pprint(change)
