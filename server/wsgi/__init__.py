import base64
import os

import torch
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS

from r2g.mrg_main import MRG

load_dotenv()
CURRENT_DIR = os.getcwd()

init_MRG = MRG()

app = Flask(__name__)
CORS(app)

device = "cuda" if torch.cuda.is_available() else "cpu"


@app.route("/mrg", methods=["POST"])
def mrg():
    data = request.get_json()
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
    return {"mrg_result": report_result}


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=int(os.environ["PORT"]))
    except Exception as e:
        print(f"An exception occurred: {e}")
