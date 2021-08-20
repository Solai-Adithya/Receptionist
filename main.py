from app import socketio, app
import os

if __name__ == "__main__":
    socketio.run(
        app,
        host="localhost",
        port=int(os.environ.get("PORT", 5000)),
        log_output=True,
        use_reloader=True,
    )
