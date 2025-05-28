import os
import uuid
import subprocess
from flask import Flask, request, send_file, render_template

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

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

    subprocess.run([
        'spleeter', 'separate',
        '-p', 'spleeter:4stems',
        '-o', output_dir,
        input_path
    ])

    result_folder = os.path.join(output_dir, filename.replace('.mp3', ''))
    processed_path = os.path.join(result_folder, 'other.wav')

    if not os.path.exists(processed_path):
        return "Processing failed"

    return send_file(processed_path, as_attachment=True, download_name='no_drums.wav')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
