from flask import Flask, request, jsonify, send_file, render_template
import os, glob, requests, urllib.parse, time, shutil
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save

load_dotenv()
app = Flask(__name__)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    try:
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, VideoFileClip, CompositeAudioClip, TextClip, CompositeVideoClip
        
        script = request.json.get("script","")
        if not script:
            return jsonify({"error": "Script khali hai!"}), 400

        for f in glob.glob("scene_*.jpg"):
            os.remove(f)
        for f in ["voice.mp3","scriptreel_output.mp4","scriptreel_final.mp4","bg_music.mp3"]:
            if os.path.exists(f): os.remove(f)

        audio = client.text_to_speech.convert(
            text=script,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        save(audio, "voice.mp3")

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

        audio_clip = AudioFileClip("voice.mp3")
        total_dur = audio_clip.duration
        scene_files = sorted(glob.glob("scene_*.jpg"))
        dur_per = total_dur / len(scene_files)
        clips = [ImageClip(sf).with_duration(dur_per) for sf in scene_files]
        video = concatenate_videoclips(clips).with_audio(audio_clip)

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
                        font="Arial",
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

        video.write_videofile("scriptreel_final.mp4", fps=24, codec="libx264", audio_codec="aac")

        return jsonify({"success": True, "file": "scriptreel_final.mp4"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download")
def download():
    return send_file("scriptreel_final.mp4", as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)