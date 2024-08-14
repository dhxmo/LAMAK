import base64
import os
import time

import socketio

from gui.utils import shared_state

sio = socketio.Client(reconnection=True, reconnection_delay=5)
LAST_HEARTBEAT = time.time()


@sio.event
def connect():
    print("client connected!")


@sio.on("connected")
def connected(data):
    print(f"connected {data['data']}")

@sio.on("mrg_result")
def send_brain_image(data):
    print("received video_data")

    # Decode the Base64 encoded video data
    shared_state["mrg_ready"] = True
    shared_state["report"] = data["mrg_result"]
