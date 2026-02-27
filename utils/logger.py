from datetime import datetime
import os

LOG_DIR = "output"
LOG_FILE = os.path.join(LOG_DIR, "logs.txt")

def log(message):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
