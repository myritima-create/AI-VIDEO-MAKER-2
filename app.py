import os, sys, json, re, asyncio, subprocess, tempfile, glob, urllib.parse, time
import requests, streamlit as st, edge_tts, anthropic
from moviepy.editor import (ImageClip, AudioFileClip, VideoFileClip,
                            CompositeVideoClip, concatenate_videoclips)

st.set_page_config(page_title="AI Video Maker", page_icon="🎬", layout="centered")
st.title("🎬 AI Video Maker")
st.caption("Script → voiceover → AI visuals → video. 2 / 3 / 5 / 10 minutes, with or without a face.")

VOICES = {
    "English (US) – Jenny": ("en-US-JennyNeural", "English"),
    "English (India) – Neerja": ("en-IN-NeerjaNeural", "English"),
    "Hindi – Swara": ("hi-IN-SwaraNeural", "Hindi"),
    "Hindi – Madhur": ("hi-IN-MadhurNeural", "Hindi"),
}

with st.sidebar:
    st.header("Settings")
    minutes = st.selectbox("Video length (minutes)", [2, 3, 5, 10])
    mode = st.radio("Face", ["Without face (visuals + voice)", "With face (talking head)"])
    layout = "Picture-in-picture"
    face_file = None
    if mode.startswith("With"):
        face_file = st.file_uploader("Upload a clear front-facing photo", type=["png", "jpg", "jpeg"])
        layout = st.radio("Face layout", ["Picture-in-picture", "Full screen"])
    voice_label = st.selectbox("Voice / language", list(VOICES))
    ratio = st.radio("Format", ["16:9 (YouTube)", "9:16 (Reels/Shorts)"])
    style = st.text_input("Visual style", "cinematic, realistic, high detail")
    api_key = st.text_input("Anthropic API key", type="password",
                            value=os.environ.get("ANTHROPIC_API_KEY", ""))

topic = st.text_area("Video topic / idea", placeholder="e.g. 5 study habits of toppers")
go = st.button("Generate video", type="primary", disabled=not topic.strip())

W, H = (1280, 720) if ratio.startswith("16") else (720, 1280)


def make_script(topic, minutes, language):
    total_words = minutes * 140
    n = max(4, round(minutes * 60 / 12))
    prompt = (
        f"Write a {minutes}-minute video script about: {topic}\n"
        f"Language: {language}. About {total_words} words total, split into exactly {n} scenes "
        f"of ~{total_words // n} words each. Engaging hook first, clear ending last.\n"
        f"Return ONLY a JSON list: [{{\"narration\": \"...\", \"image_prompt\": \"English visual description\"}}]"
    )
    client = anthropic.Anthropic(api_key=api_key)
    r = client.messages.create(model="claude-sonnet-5-5", max_tokens=8000,
                               messages=[{"role": "user", "content": prompt}])
    txt = re.sub(r"^```(?:json)?|```$", "", r.content[0].text.strip(), flags=re.M).strip()
    return json.loads(txt)


def tts(text, voice, path):
    asyncio.run(edge_tts.Communicate(text, voice).save(path))


def get_image(prompt, path, seed):
    url = (f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
           f"?width={W}&height={H}&nologo=true&seed={seed}")
    for _ in range(3):
        try:
            r = requests.get(url, timeout=120)
            if r.ok and r.content:
                open(path, "wb").write(r.content)
                return
        except requests.RequestException:
            pass
        time.sleep(3)
    raise RuntimeError("Image generation failed for: " + prompt[:60])


def talking_head(face, audio, outdir):
    sd = os.environ.get("SADTALKER_DIR")
    if not sd:
        raise RuntimeError("Set SADTALKER_DIR to your SadTalker folder (see README).")
    py = os.environ.get("SADTALKER_PY", "python")
    subprocess.run([py, "inference.py", "--driven_audio", os.path.abspath(audio),
                    "--source_image", os.path.abspath(face), "--result_dir", os.path.abspath(outdir),
                    "--still", "--preprocess", "full"], cwd=sd, check=True)
    return max(glob.glob(os.path.join(outdir, "**", "*.mp4"), recursive=True), key=os.path.getmtime)


def visual_clip(img, dur):
    c = ImageClip(img).set_duration(dur).resize(lambda t: 1 + 0.06 * t / dur)
    return CompositeVideoClip([c.set_position("center")], size=(W, H)).set_duration(dur)


if go:
    voice, language = VOICES[voice_label]
    if mode.startswith("With") and face_file is None:
        st.error("Please upload a face photo."); st.stop()
    work = tempfile.mkdtemp()
    face_path = None
    if face_file:
        face_path = os.path.join(work, "face.png")
        open(face_path, "wb").write(face_file.getvalue())
    bar, status = st.progress(0.0), st.empty()
    try:
        status.info("Writing script…")
        scenes = make_script(topic, minutes, language)
        clips = []
        for i, s in enumerate(scenes):
            status.info(f"Scene {i + 1}/{len(scenes)}: voice + visuals…")
            a_path, i_path = f"{work}/a{i}.mp3", f"{work}/i{i}.jpg"
            tts(s["narration"], voice, a_path)
            audio = AudioFileClip(a_path)
            base = visual_clip(i_path if get_image(f"{s['image_prompt']}, {style}", i_path, i) is None else i_path,
                               audio.duration)
            if face_path:
                status.info(f"Scene {i + 1}/{len(scenes)}: animating face (slow)…")
                head = VideoFileClip(talking_head(face_path, a_path, f"{work}/h{i}"))
                if layout == "Full screen":
                    scene = head.resize(height=H).set_position("center")
                    base = CompositeVideoClip([base, scene], size=(W, H))
                else:
                    head = head.resize(height=int(H * 0.38)).set_position(("right", "bottom"))
                    base = CompositeVideoClip([base, head], size=(W, H))
            clips.append(base.set_audio(audio).set_duration(audio.duration))
            bar.progress((i + 1) / len(scenes) * 0.9)
        status.info("Rendering final video…")
        out = os.path.join(work, "video.mp4")
        concatenate_videoclips(clips, method="compose").write_videofile(
            out, fps=24, codec="libx264", audio_codec="aac", preset="veryfast", logger=None)
        bar.progress(1.0); status.success("Done!")
        st.video(out)
        st.download_button("Download MP4", open(out, "rb").read(), "ai_video.mp4", "video/mp4")
        with st.expander("Script"):
            for s in scenes: st.write(s["narration"])
    except Exception as e:
        status.error(f"Failed: {e}")
