import os, sys, socket, threading, webbrowser
import anthropic, edge_tts, requests, moviepy.editor  # noqa: lets PyInstaller find them
from streamlit.web import bootstrap

def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()

if __name__ == "__main__":
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    print(f"\nAI Video Maker running.\n  This PC : http://localhost:8501\n  Android : http://{lan_ip()}:8501  (same Wi-Fi)\n")
    threading.Timer(4, lambda: webbrowser.open("http://localhost:8501")).start()
    bootstrap.run(os.path.join(base, "app.py"), False, [], {
        "server.headless": True, "server.port": 8501, "server.address": "0.0.0.0",
        "global.developmentMode": False, "browser.gatherUsageStats": False})
