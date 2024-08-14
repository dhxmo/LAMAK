import os
from tkinter import Tk
from dotenv import load_dotenv
load_dotenv()


from gui.lamak_gui import Application
from gui.ws_client import sio

if __name__ == "__main__":
    try:
        sio.connect(os.environ["URL"])

        root = Tk()
        app = Application(root)
        root.mainloop()
    except Exception as e:
        print("Exception in main loop", str(e))