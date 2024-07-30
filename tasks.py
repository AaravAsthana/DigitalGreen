from celery import Celery
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
from celery_config import make_celery  # Import make_celery from celery_config
import json

# # Initialize Flask app
# app = Flask(__name__)
# app.config.update(
#     CELERY_BROKER_URL=os.getenv("CELERY_BROKER_URL", "redis://localhost:6380/0"),
#     CELERY_RESULT_BACKEND=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6380/0")
# )

# celery = make_celery(app)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

celery = Celery(__name__, broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6380/0"))
celery.conf.update(
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6380/0")
)

# Ensure NumPy compatibility
import numpy as np
np.__version__  # Check NumPy version
if int(np.__version__.split('.')[0]) >= 2:
    raise ImportError("The script requires NumPy version < 2.0.0")

# Function to download YouTube video using yt-dlp
def download_youtube_video(url, output_path, audio_only=False):
    ydl_opts = {
        'format': 'bestaudio/best' if audio_only else 'best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            return filename
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        return None

# Function to download audio or video from other links
def download_audio_video_from_link(url, output_path):
    local_filename = os.path.join(output_path, url.split('/')[-1])
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename
    except Exception as e:
        print(f"Error downloading file: {e}")   
        return None
    
# Function to extract audio using pydub
def extract_audio_from_video(video_path, audio_path):
    try:
        audio = AudioSegment.from_file(video_path)
        audio.export(audio_path, format="mp3")
    except Exception as e:
        print(f"Error extracting audio: {e}")

# Function to transcribe audio using OpenAI Whisper
def transcribe_audio(audio_path, language="en"):
    model = whisper.load_model("large")
    result = model.transcribe(audio_path, language=language)
    return result["text"]

# Function to save text as a file
def save_text_as_file(text, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)

# Function to split text into chunks
def split_text(text, max_tokens=1500):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += 1

        if current_length >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Function to summarize text using OpenAI
def summarize_text(text):
    text_chunks = split_text(text)
    file_summary = ""
    for chunk in text_chunks:
         # Make the request to the OpenAI API for summary
        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "You are an agricultural expert. Summarize the provided text."},
                {"role": "user", "content": f"Summarize the following text: {chunk}"}
            ]
        )
        file_summary += summary_response.choices[0].message.content + "\n"
    return file_summary

# Function to classify text using OpenAI
def classify_text(summary_text):
    classification_content = f"""
    Please classify the following text into one or more of these specific crop-related classes: 
    ['paddy', 'wheat', 'ragi', 'garlic', 'maize', 'peas', 'cabbage', 'pumpkin', 'none'].

    Criteria for classification:
    - 'paddy': Information related to paddy or rice crops.
    - 'wheat': Information related to wheat crops.
    - 'ragi': Information related to ragi crops.
    - 'garlic': Information related to garlic crops.
    - 'maize': Information related to maize or corn crops.
    - 'peas': Information related to pea crops.
    - 'cabbage': Information related to cabbage crops.
    - 'pumpkin': Information related to pumpkin crops.
    - 'none': Only use this if the text does not relate to any of the above crops.

    Important:
    - If the text contains information about multiple crops, list all applicable classes separated by commas.
    - Only use the 'none' class if none of the other classes apply.
    - Do not provide any explanations, only list the class names separated by commas.

    Text to evaluate: {summary_text}

    Provide only the class names as output, separated by commas.
    """
    classification_response = client.chat.completions.create(
        model="gpt-3.5-turbo-0301",
        messages=[
            {"role": "system", "content": """
                You are an expert in agricultural text classification. Your task is to accurately classify text segments based on specific crop-related categories. 
                You will be provided with text, and you must classify it into one or more of the following categories: 
                'paddy', 'wheat', 'ragi', 'garlic', 'maize', 'peas', 'cabbage', 'pumpkin', or 'none'.
                - 'paddy': Classify this if the text contains any information related to paddy or rice crops.
                - 'wheat': Classify this if the text contains any information related to wheat crops.
                - 'ragi': Classify this if the text contains any information related to ragi crops.
                - 'garlic': Classify this if the text contains any information related to garlic crops.
                - 'maize': Classify this if the text contains any information related to maize or corn crops.
                - 'peas': Classify this if the text contains any information related to pea crops.
                - 'cabbage': Classify this if the text contains any information related to cabbage crops.
                - 'pumpkin': Classify this if the text contains any information related to pumpkin crops.
                - 'none': Only use this if the text does not relate to any of the other classes.
                If multiple classes apply, list all applicable classes separated by commas. Do not provide any explanations, only the class names.
            """},
            {"role": "user", "content": classification_content}
        ]
    )
    result = classification_response.choices[0].message.content.strip()
    result_classes = [cls.strip() for cls in result.split(",") if cls.strip()]
    if len(result_classes) > 1 and 'none' in result_classes:
        result_classes.remove('none')
    return result_classes

# Celery task to process files
@celery.task(bind=True)
def process_files(self, file_paths):
    pdf_directory_path = "./pdfs"
    os.makedirs(pdf_directory_path, exist_ok=True)

    cumulative_summary = ""
    all_classes = {}

    # Step 1: Process URLs from urls.txt
    urls_file_path = os.path.join(pdf_directory_path, "urls.txt")
    if os.path.exists(urls_file_path):
        with open(urls_file_path, 'r') as urls_file:
            urls = urls_file.readlines()
    else:
        urls = []

    for url in urls:
        url = url.strip()
        filename = os.path.basename(url).split('?')[0]
        file_path = os.path.join(pdf_directory_path, filename)

        if "youtube.com" in url or "youtu.be" in url:
            video_path = download_youtube_video(url, pdf_directory_path, audio_only=True)
            if video_path:
                audio_path = os.path.join(pdf_directory_path, filename.rsplit('.', 1)[0] + '.wav')
                extract_audio_from_video(video_path, audio_path)
            else:
                continue
        else:
            download_audio_video_from_link(url, file_path)

    # Step 2: Extract audio from all videos
    for filename in os.listdir(pdf_directory_path):
        if filename.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.mkv', '.avi', '.mov')):
            if filename.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                audio_path = os.path.join(pdf_directory_path, filename.rsplit('.', 1)[0] + '.wav')
                extract_audio_from_video(os.path.join(pdf_directory_path, filename), audio_path)
            else:
                audio_path = os.path.join(pdf_directory_path, filename)
            
            transcription = transcribe_audio(audio_path)
            transcription_file_path = os.path.join(pdf_directory_path, filename.rsplit('.', 1)[0] + '.txt')
            save_text_as_file(transcription, transcription_file_path)

    # Step 3: Process text and PDF files from file_paths
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        if filename.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.mkv', '.avi', '.mov')):
            continue
        elif filename in ['urls.txt' , 'url.txt' ]:
            continue
        elif filename.endswith(".pdf") or filename.endswith(".txt"):
            file_text = ""

            if filename.endswith(".pdf"):
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page_num in range(len(pdf_reader.pages)):
                        page_text = pdf_reader.pages[page_num].extract_text()
                        file_text += page_text.lower() + " "
            else:
                with open(file_path, 'r', encoding='utf-8') as text_file:
                    file_text = text_file.read().lower()

        file_summary = summarize_text(file_text)
        cumulative_summary += file_summary + "\n"
        file_classes = classify_text(file_summary)
        all_classes[filename] = file_classes

    return {"summary": cumulative_summary, "classes": all_classes}