import os
import uuid
import subprocess
from flask import Flask, request, send_file, render_template
from pydub import AudioSegment
from youtubesearchpython import VideosSearch
from flask import jsonify, request
from pytube import YouTube


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/youtube_search')
def youtube_search():
    query = request.args.get('q')
    if not query:
        return jsonify([])

    results = VideosSearch(query, limit=5).result()['result']
    videos = [{
        'title': v['title'],
        'video_id': v['id'],
        'thumbnail': v['thumbnails'][0]['url']
    } for v in results]

    return jsonify(videos)

@app.route('/process_youtube')
def process_youtube():
    video_id = request.args.get('video_id')
    if not video_id:
        return "Missing video_id", 400

    try:
        print("🔍 Downloading from YouTube...")
        try:
            yt = YouTube(f"https://youtube.com/watch?v={video_id}")
        except Exception as e:
            return f"Failed to initialize YouTube object: {e}", 500

        stream = yt.streams.filter(only_audio=True).first()
        print("✅ Stream selected:", stream)

        temp_folder = os.path.join("uploads", str(uuid.uuid4()))
        os.makedirs(temp_folder, exist_ok=True)

        audio_path = os.path.join(temp_folder, f"{yt.title}.mp3")
        print("📥 Saving to:", audio_path)
        stream.download(output_path=temp_folder, filename=f"{yt.title}.mp3")

        # Reuse the existing process logic
        output_dir = os.path.join("processed", str(uuid.uuid4()))
        os.makedirs(output_dir, exist_ok=True)

        subprocess.run([
            'spleeter', 'separate',
            '-p', 'spleeter:4stems',
            '-o', output_dir,
            audio_path
        ], check=True)

        # Mixing tracks
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        result_folder = os.path.join(output_dir, base_name)

        vocals = AudioSegment.from_wav(os.path.join(result_folder, 'vocals.wav'))
        bass = AudioSegment.from_wav(os.path.join(result_folder, 'bass.wav'))
        other = AudioSegment.from_wav(os.path.join(result_folder, 'other.wav'))

        combined = vocals.overlay(bass).overlay(other)
        output_mix_path = os.path.join(result_folder, 'no_drums.wav')
        combined.export(output_mix_path, format='wav')

        return send_file(output_mix_path, as_attachment=True, download_name='no_drums.wav')

    except Exception as e:
        return f"Failed: {e}", 500

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files or request.files['file'].filename == '':
        return 'No file uploaded.'

    file = request.files['file']
    filename = file.filename
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    unique_id = str(uuid.uuid4())
    output_dir = os.path.join(PROCESSED_FOLDER, unique_id)
    os.makedirs(output_dir, exist_ok=True)

    try:
        subprocess.run([
            'spleeter', 'separate',
            '-p', 'spleeter:4stems',
            '-o', output_dir,
            input_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        return f"Spleeter failed: {e}"

    # Resolve actual folder name from filename (remove .mp3 or any extension)
    base_name = os.path.splitext(filename)[0]
    result_folder = os.path.join(output_dir, base_name)

    # Compose mixed output (vocals + bass + other)
    vocals_path = os.path.join(result_folder, 'vocals.wav')
    bass_path = os.path.join(result_folder, 'bass.wav')
    other_path = os.path.join(result_folder, 'other.wav')
    output_mix_path = os.path.join(result_folder, 'no_drums.wav')

    try:
        vocals = AudioSegment.from_wav(vocals_path)
        bass = AudioSegment.from_wav(bass_path)
        other = AudioSegment.from_wav(other_path)
        combined = vocals.overlay(bass).overlay(other)
        combined.export(output_mix_path, format='wav')
    except Exception as e:
        return f"Audio merging failed: {e}"

    if not os.path.exists(output_mix_path):
        return "Processing failed"

    return send_file(output_mix_path, as_attachment=True, download_name='no_drums.wav')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
