import os
import requests
import PyPDF2
from dotenv import load_dotenv
import openai
import whisper
import subprocess
from fpdf import FPDF
import yt_dlp as youtube_dl
from pydub import AudioSegment
from flask import Flask, request, jsonify
from celery_config import make_celery  # Import make_celery from celery_config
from werkzeug.utils import secure_filename
import json
import numpy as np  # Ensure NumPy compatibilitys
from tasks import process_files,celery
from celery.result import AsyncResult

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Flask app
app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL=os.getenv("CELERY_BROKER_URL", "redis://localhost:6380/0"),
    CELERY_RESULT_BACKEND=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6380/0"),
)

celery.conf.update(app.config)

UPLOAD_FOLDER = './temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part in the request'}), 400

    files = request.files.getlist('files')
    file_paths = []

    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        file_paths.append(file_path)

    task = process_files.delay(file_paths)
    return jsonify({'task_id': task.id}), 202

@app.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = AsyncResult(task_id, app=celery)
    response = {
        'task_id': task_id,
        'task_status': task.status,
        'task_result': task.result if task.status == 'SUCCESS' else None
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)