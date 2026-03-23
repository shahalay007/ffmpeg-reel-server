from flask import Flask, request, jsonify, send_file
import subprocess
import os
import uuid
import textwrap

app = Flask(__name__)
OUTPUT_DIR = "/tmp/reels"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def wrap_text(text, width=35):
    return '\n'.join(textwrap.wrap(text, width))

def generate_reel(topic, caption, script):
    video_id = str(uuid.uuid4())[:8]
    output_path = f"{OUTPUT_DIR}/{video_id}.mp4"

    topic_safe = topic.replace("'", "").replace(":", "").upper()[:50]
    caption_safe = caption.replace("'", "").replace(":", "")[:200]
    script_safe = script.replace("'", "").replace(":", "")[:300]

    topic_wrapped = wrap_text(topic_safe, 28)
    caption_lines = wrap_text(caption_safe, 32)
    script_lines = wrap_text(script_safe, 38)

    vf = (
        f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.6:t=fill,"
        f"drawtext=text='{topic_wrapped}':fontsize=52:fontcolor=white:"
        f"x=(w-text_w)/2:y=120:font=DejaVuSans-Bold:shadowcolor=black:shadowx=3:shadowy=3:line_spacing=10,"
        f"drawtext=text='{caption_lines}':fontsize=28:fontcolor=yellow:"
        f"x=60:y=500:font=DejaVuSans:shadowcolor=black:shadowx=2:shadowy=2:line_spacing=8,"
        f"drawtext=text='SCRIPT':fontsize=22:fontcolor=gray:x=60:y=900:font=DejaVuSans-Bold,"
        f"drawtext=text='{script_lines}':fontsize=24:fontcolor=white:"
        f"x=60:y=940:font=DejaVuSans:shadowcolor=black:shadowx=1:shadowy=1:line_spacing=7,"
        f"drawtext=text='Tech/AI Daily':fontsize=20:fontcolor=blue:x=(w-text_w)/2:y=1800:font=DejaVuSans-Bold"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x0a0a1a:size=1080x1920:duration=30:rate=30",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-t", "30", "-pix_fmt", "yuv420p",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr[-500:]}")

    return output_path, video_id

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "service": "FFmpeg Reel Generator"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    topic = data.get("topic", "Tech/AI")
    caption = data.get("caption", "")
    script = data.get("script", "")

    try:
        output_path, video_id = generate_reel(topic, caption, script)
        domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
        if domain:
            video_url = f"https://{domain}/video/{video_id}"
        else:
            video_url = f"/video/{video_id}"
        return jsonify({"success": True, "video_id": video_id, "video_url": video_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/video/<video_id>", methods=["GET"])
def serve_video(video_id):
    path = f"{OUTPUT_DIR}/{video_id}.mp4"
    if not os.path.exists(path):
        return jsonify({"error": "Video not found"}), 404
    return send_file(path, mimetype="video/mp4", as_attachment=True,
                     download_name=f"reel_{video_id}.mp4")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
