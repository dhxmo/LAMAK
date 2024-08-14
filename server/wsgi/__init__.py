import base64
import os

import torch
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from r2g.mrg_main import MRG

load_dotenv()
CURRENT_DIR = os.getcwd()

init_MRG = MRG()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(
    app,
    async_mode="eventlet",
    cors_allowed_origins=[os.environ["ALLOWED_HOST"]],
    ping_interval=25000,
    ping_timeout=60000,
)

device = "cuda" if torch.cuda.is_available() else "cpu"

@socketio.on("connect")
def connected():
    print("client connected")
    emit("connected", {"data": f"id: {request.sid} is connected"})


# @app.route("/mrg", methods=["POST"])
@socketio.on("mrg")
def mrg(data):
    print("data", data)

    # Decode the base64 string
    decoded_data = base64.b64decode(data["encoded_img"])

    assets_dir = f"{CURRENT_DIR}/assets/{data['unique_uuid']}"
    os.makedirs(assets_dir, exist_ok=True)

    # Save the file
    img_file_path = f"{assets_dir}/{data['unique_uuid']}.png"
    with open(img_file_path, "wb") as f:
        f.write(decoded_data)

    # pass to mrg pipeline
    report_result = init_MRG.get_report(img_file_path)
    report_file_path = f"{assets_dir}/{data['unique_uuid']}.txt"
    with open(report_file_path, "wb") as f:
        f.write(report_result)

    # send response back
    emit("mrg_result", {"mrg_result": report_result})


@socketio.on("disconnect")
def disconnected():
    """event listener when client disconnects to the server"""
    emit("disconnect", f"user {request.sid} disconnected", broadcast=True)
    print("user disconnected")


@socketio.on_error()
def error_handler(e):
    print(f"Error in socket conn occurred: {e}")


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=int(os.environ["PORT"]))
        socketio.run(
            app,
            host="0.0.0.0",
            port=int(os.environ["PORT"]),
            use_reloader=True,
            log_output=True,
        )
    except Exception as e:
        print(f"An exception occurred: {e}")
