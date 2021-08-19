from app import socketio, app

if __name__ == "__main__":
    # listenUpdate(ParticipantsCollection)
    socketio.run(
        app, host="localhost", port=5000, log_output=True, use_reloader=True
    )
