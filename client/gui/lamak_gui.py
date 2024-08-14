import base64
import json
import os
import uuid

from tkinter import *
import pyautogui
import requests
from dotenv import load_dotenv

load_dotenv()


class Application:
    def __init__(self, master):
        self.master = master

        self.snip_surface = None
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None

        master.geometry("400x600")  # set new geometry
        master.title("Röntgen")

        self.menu_frame = Frame(master)
        self.menu_frame.pack(fill=BOTH, expand=YES, padx=1, pady=1)

        self.buttonBar = Frame(self.menu_frame, bg="")
        self.buttonBar.pack()

        self.snipButton = Button(
            self.buttonBar,
            text="Capture here",
            width=15,
            height=5,
            command=self.create_screen_canvas,
        )
        self.snipButton.pack()

        # Create the text area
        self.text_area = Text(self.master, height=100, width=50)
        self.text_area.pack(padx=20, pady=20)

        self.master_screen = Toplevel(master)
        self.master_screen.withdraw()

        self.picture_frame = Frame(self.master_screen)
        self.picture_frame.pack(fill=BOTH, expand=YES)

        self.CURR_DIR = os.getcwd()
        self.assets_dir = f"{self.CURR_DIR}/assets"
        os.makedirs(self.assets_dir, exist_ok=True)

    def create_screen_canvas(self):
        self.master_screen.deiconify()
        self.master.withdraw()

        self.snip_surface = Canvas(self.picture_frame, cursor="cross", bg="grey11")
        self.snip_surface.pack(fill=BOTH, expand=YES)

        self.snip_surface.bind("<ButtonPress-1>", self.on_button_press)
        self.snip_surface.bind("<B1-Motion>", self.on_snip_drag)
        self.snip_surface.bind("<ButtonRelease-1>", self.on_button_release)

        self.master_screen.attributes("-fullscreen", True)
        self.master_screen.attributes("-alpha", 0.3)
        self.master_screen.lift()
        self.master_screen.attributes("-topmost", True)

    def take_bounded_screenshot(self, x1, y1, x2, y2):
        image = pyautogui.screenshot(region=(int(x1), int(y1), int(x2), int(y2)))
        random_uuid = str(uuid.uuid4())
        img_file_path = f"{self.assets_dir}/{random_uuid}.png"
        image.save(img_file_path)

        # base64 encode image
        with open(img_file_path, "rb") as img:
            # Read the audio file as bytes
            audio_data = img.read()

            # Encode the audio data in base64
            encoded_img = base64.b64encode(audio_data).decode("utf-8")

            headers = {"Content-Type": "application/json"}
            data = {
                "unique_uuid": random_uuid,
                "encoded_img": encoded_img
            }
            data = json.dumps(data)

            res = requests.post(url=os.environ["SERVER_IP"], data=data, headers=headers)
            res = json.loads(res.text)
            report = res["mrg_result"]

            # paste response to box
            self.text_area.insert(END, report)

    def on_button_release(self, event):
        if self.start_x <= self.current_x and self.start_y <= self.current_y:
            self.take_bounded_screenshot(
                self.start_x,
                self.start_y,
                self.current_x - self.start_x,
                self.current_y - self.start_y,
            )

        elif self.start_x >= self.current_x and self.start_y <= self.current_y:
            self.take_bounded_screenshot(
                self.current_x,
                self.start_y,
                self.start_x - self.current_x,
                self.current_y - self.start_y,
            )

        elif self.start_x <= self.current_x and self.start_y >= self.current_y:
            self.take_bounded_screenshot(
                self.start_x,
                self.current_y,
                self.current_x - self.start_x,
                self.start_y - self.current_y,
            )

        elif self.start_x >= self.current_x and self.start_y >= self.current_y:
            self.take_bounded_screenshot(
                self.current_x,
                self.current_y,
                self.start_x - self.current_x,
                self.start_y - self.current_y,
            )

        self.exit_screenshot_mode()
        return event

    def exit_screenshot_mode(self):
        self.snip_surface.destroy()
        self.master_screen.withdraw()
        self.master.deiconify()

    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = self.snip_surface.canvasx(event.x)
        self.start_y = self.snip_surface.canvasy(event.y)
        self.snip_surface.create_rectangle(0, 0, 1, 1, outline="red", width=3)

    def on_snip_drag(self, event):
        self.current_x, self.current_y = (event.x, event.y)
        # expand rectangle as you drag the mouse
        self.snip_surface.coords(
            1, self.start_x, self.start_y, self.current_x, self.current_y
        )
