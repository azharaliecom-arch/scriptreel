import os
import requests
import urllib.parse
import glob
import time
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from moviepy import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    VideoFileClip, CompositeAudioClip, TextClip, CompositeVideoClip
)

load_dotenv()

ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_KEY)

def script_to_voice(script_text):
    print("🎙️ Voice ban rahi hai...")
    audio = client.text_to_speech.convert(
        text=script_text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    save(audio, "voice.mp3")
    print("✅ Voice ready!")

def script_to_images(script_text):
    print("🎨 AI Images ban rahi hain...")
    scenes = script_text.split(".")
    scenes = [s.strip() for s in scenes if len(s.strip()) > 10]
    image_urls = [
        "https://picsum.photos/1280/720?random=1",
        "https://picsum.photos/1280/720?random=2",
        "https://picsum.photos/1280/720?random=3",
        "https://picsum.photos/1280/720?random=4",
        "https://picsum.photos/1280/720?random=5",
    ]
    for i, scene in enumerate(scenes[:5]):
        print(f"  Scene {i+1} ban rahi hai...")
        try:
            response = requests.get(image_urls[i], timeout=30, allow_redirects=True)
            if response.status_code == 200:
                with open(f"scene_{i+1}.jpg", "wb") as f:
                    f.write(response.content)
                print(f"  ✅ scene_{i+1}.jpg ready!")
        except Exception as e:
            print(f"  ❌ Scene {i+1} skip: {e}")

def create_video(script_text):
    print("🎬 Video ban rahi hai...")
    audio = AudioFileClip("voice.mp3")
    total_duration = audio.duration
    scene_files = sorted(glob.glob("scene_*.jpg"))
    if not scene_files:
        print("❌ Koi scene nahi mila!")
        return
    duration_per_scene = total_duration / len(scene_files)
    clips = []
    for i, scene_file in enumerate(scene_files):
        clip = ImageClip(scene_file).with_duration(duration_per_scene)
        clips.append(clip)
        print(f"  ✅ Scene {i+1} add ho gayi!")
    final_video = concatenate_videoclips(clips)
    final_video = final_video.with_audio(audio)

    # SUBTITLES
    print("💬 Subtitles add ho rahi hain...")
    sentences = [s.strip() for s in script_text.split(".") if len(s.strip()) > 10]
    subtitle_clips = []
    subtitle_duration = total_duration / len(sentences)
    for i, sentence in enumerate(sentences):
        words = sentence.split()
        short = " ".join(words[:8])
        try:
            txt_clip = (
                TextClip(
                    text=short,
                    font_size=36,
                    color="white",
                    stroke_color="black",
                    stroke_width=2,
                    font="C:/Windows/Fonts/arial.ttf",
                    method="caption",
                    size=(1100, None),
                )
                .with_start(i * subtitle_duration)
                .with_duration(subtitle_duration)
                .with_position(("center", 0.85), relative=True)
            )
            subtitle_clips.append(txt_clip)
            print(f"  ✅ Subtitle {i+1} ready!")
        except Exception as e:
            print(f"  ⚠️ Subtitle {i+1} skip: {e}")
    if subtitle_clips:
        final_video = CompositeVideoClip([final_video] + subtitle_clips)

    print("⏳ Render ho raha hai...")
    final_video.write_videofile(
        "scriptreel_output.mp4",
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )
    print("✅ Video ready!")

def add_background_music():
    print("🎵 BG Music add ho rahi hai...")
    try:
        # Local free music download
        music_url = "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Tours/Enthusiast/Tours_-_01_-_Enthusiast.mp3"
        music_response = requests.get(music_url, timeout=90)
        with open("bg_music.mp3", "wb") as f:
            f.write(music_response.content)

        video = VideoFileClip("scriptreel_output.mp4")
        bg_music = AudioFileClip("bg_music.mp3")
        bg_music = bg_music.subclipped(0, video.duration)
        bg_music = bg_music.with_volume_scaled(0.12)
        final_audio = CompositeAudioClip([video.audio, bg_music])
        final_video = video.with_audio(final_audio)
        final_video.write_videofile(
            "scriptreel_final.mp4",
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )
        print("✅ BG Music ready!")
    except Exception as e:
        print(f"⚠️ Music skip — video without music save ho rahi hai: {e}")
        import shutil
        shutil.copy("scriptreel_output.mp4", "scriptreel_final.mp4")
        print("✅ Video without music bhi ready hai!")

if __name__ == "__main__":
    for f in glob.glob("scene_*.jpg"):
        os.remove(f)
    for f in ["voice.mp3", "scriptreel_output.mp4",
              "scriptreel_final.mp4", "bg_music.mp3"]:
        if os.path.exists(f):
            os.remove(f)
    print("✅ Clean! Ab naya bana raha hai...")
    script = input("🎬 Apna script likho: ")
    script_to_voice(script)
    script_to_images(script)
    create_video(script)
    add_background_music()
    print("\n🎉 ScriptReel Final Video Complete!")
    print("📁 C:\\ScriptReel\\scriptreel_final.mp4")