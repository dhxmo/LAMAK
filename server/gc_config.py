import os

from dotenv import load_dotenv

load_dotenv()


# Set the number of workers to the number of CPUs available
workers = 1

# Specify the worker class to use Eventlet
worker_class = "eventlet"

# Set the timeout to 1.5 hour
timeout = 5400

# Bind Gunicorn to listen on all network interfaces on port <PORT>
bind = f"0.0.0.0:{os.environ['PORT']}"
