# AI Video Maker – Windows app + Android app

Windows runs the engine (script, voice, images, video, face). The Android app is a
window to it: you type the PC's address, make videos from your phone, and download the MP4.
(Video rendering and face animation can't run on a phone.)

## Get the .exe and .apk (no installs needed)
1. Create a free GitHub repository and upload everything in this folder
   (keep the `.github` folder).
2. Open the **Actions** tab. Both builds start automatically (about 10 to 15 minutes).
3. Open the finished run and download:
   - **AIVideoMaker-Windows**: unzip, run `AIVideoMaker.exe`
   - **AIVideoMaker-Android-apk**: copy to the phone and install (allow "unknown sources")

## Using it
1. Run `AIVideoMaker.exe` on the PC. A console shows two addresses.
2. Allow Windows Firewall access when asked (needed for the phone).
3. PC: the browser opens by itself. Phone: open the app, type the Android address
   shown in the console (like `192.168.1.5:8501`), tap Go. Phone and PC must be on the same Wi-Fi.
4. Paste your Anthropic API key in the sidebar, choose length and face option, generate.

## Face mode
Needs SadTalker installed on the PC (see the earlier README steps) and the
`SADTALKER_DIR` environment variable set. Without it, use "Without face".

## Run from source instead
pip install streamlit anthropic edge-tts requests moviepy==1.0.3 Pillow==9.5.0
python launcher.py
