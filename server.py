from flask import Flask, request, jsonify, send_file, render_template
import os, glob, requests, urllib.parse, time, shutil
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from moviepy import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    VideoFileClip, CompositeAudioClip, TextClip, CompositeVideoClip
)

load_dotenv()
app = Flask(__name__)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def generate_video(script):
    for f in glob.glob("scene_*.jpg"):
        os.remove(f)
    for f in ["voice.mp3","scriptreel_output.mp4","scriptreel_final.mp4","bg_music.mp3"]:
        if os.path.exists(f): os.remove(f)

    # VOICE
    audio = client.text_to_speech.convert(
        text=script,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    save(audio, "voice.mp3")

    # IMAGES
    scenes = [s.strip() for s in script.split(".") if len(s.strip()) > 10]
    image_urls = [
        "https://picsum.photos/1280/720?random=1",
        "https://picsum.photos/1280/720?random=2",
        "https://picsum.photos/1280/720?random=3",
        "https://picsum.photos/1280/720?random=4",
        "https://picsum.photos/1280/720?random=5",
    ]
    for i, scene in enumerate(scenes[:5]):
        try:
            r = requests.get(image_urls[i], timeout=30, allow_redirects=True)
            if r.status_code == 200:
                with open(f"scene_{i+1}.jpg","wb") as f:
                    f.write(r.content)
        except: pass

    # VIDEO
    audio_clip = AudioFileClip("voice.mp3")
    total_dur = audio_clip.duration
    scene_files = sorted(glob.glob("scene_*.jpg"))
    dur_per = total_dur / len(scene_files)
    clips = [ImageClip(sf).with_duration(dur_per) for sf in scene_files]
    video = concatenate_videoclips(clips).with_audio(audio_clip)

    # SUBTITLES
    sentences = [s.strip() for s in script.split(".") if len(s.strip()) > 10]
    sub_dur = total_dur / len(sentences)
    sub_clips = []
    for i, sentence in enumerate(sentences):
        short = " ".join(sentence.split()[:8])
        try:
            txt = (
                TextClip(
                    text=short, font_size=36,
                    color="white", stroke_color="black",
                    stroke_width=2,
                    font="C:/Windows/Fonts/arial.ttf",
                    method="caption", size=(1100, None),
                )
                .with_start(i * sub_dur)
                .with_duration(sub_dur)
                .with_position(("center", 0.85), relative=True)
            )
            sub_clips.append(txt)
        except: pass
    if sub_clips:
        video = CompositeVideoClip([video] + sub_clips)

    video.write_videofile("scriptreel_output.mp4", fps=24, codec="libx264", audio_codec="aac")

    # MUSIC
    try:
        mr = requests.get("https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Tours/Enthusiast/Tours_-_01_-_Enthusiast.mp3", timeout=90)
        with open("bg_music.mp3","wb") as f:
            f.write(mr.content)
        v2 = VideoFileClip("scriptreel_output.mp4")
        bg = AudioFileClip("bg_music.mp3").subclipped(0, v2.duration).with_volume_scaled(0.12)
        v2.with_audio(CompositeAudioClip([v2.audio, bg])).write_videofile(
            "scriptreel_final.mp4", fps=24, codec="libx264", audio_codec="aac")
    except:
        shutil.copy("scriptreel_output.mp4","scriptreel_final.mp4")

    return "scriptreel_final.mp4"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    script = request.json.get("script","")
    if not script:
        return jsonify({"error": "Script khali hai!"}), 400
    output = generate_video(script)
    return jsonify({"success": True, "file": output})

@app.route("/download")
def download():
    return send_file("scriptreel_final.mp4", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5000)