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
# from langdetect import detect

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

# Directories and paths
pdf_directory_path = r"C:\Users\aarav\DigitalGreen\pdf"
# audio_transcripts_path = os.path.join(pdf_directory_path, "audio_transcripts")
# video_transcripts_path = os.path.join(pdf_directory_path, "video_transcripts")

# Set permissions
os.chmod(pdf_directory_path, 0o777) 

# Ensure NumPy compatibility
import numpy as np
np.__version__  # Check NumPy version
if int(np.__version__.split('.')[0]) >= 2:
    raise ImportError("The script requires NumPy version < 2.0.0")

# Ensure directories exist
# os.makedirs(audio_transcripts_path, exist_ok=True)
# os.makedirs(video_transcripts_path, exist_ok=True)    

# Initialize Whisper model
# whisper_model = whisper.load_model("base")

# Function to download file from URL
def download_file(url, output_path):
    response = requests.get(url)
    with open(output_path, 'wb') as file:
        file.write(response.content)

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

# Function to extract audio using pydub
def extract_audio_from_video(video_path, audio_path):
    try:
        audio = AudioSegment.from_file(video_path)
        audio.export(audio_path, format="mp3")
    except Exception as e:
        print(f"Error extracting audio: {e}")

# Function to transcribe audio using OpenAI Whisper
def transcribe_audio(audio_path,language="en"):
    # detected_language = detect(audio_path)
    model = whisper.load_model("large")
    result = model.transcribe(audio_path, language=language)
    return result["text"]

# Function to save text as PDF
# def save_text_as_pdf(text, pdf_path):
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.set_font("Arial", size=12)
    
#     # Encode text using 'utf-8'
#     encoded_text = text.encode('latin-1', 'replace').decode('latin-1')
#     pdf.multi_cell(0, 10, encoded_text)
#     pdf.output(pdf_path)


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

# Initialize a dictionary to collect all classes for each file
all_classes = {}
summaries = []

# Read URLs from urls.txt
urls_file_path = os.path.join(pdf_directory_path, "urls.txt")
if os.path.exists(urls_file_path):
    with open(urls_file_path, 'r') as urls_file:
        urls = urls_file.readlines()
else:
    urls = []

# Process URLs to download them in the pdf folder
for url in urls:
    url = url.strip()
    filename = os.path.basename(url).split('?')[0]  # Handle URLs with query parameters
    file_path = os.path.join(pdf_directory_path, filename)

    if "youtube.com" in url or "youtu.be" in url:
        video_path = download_youtube_video(url, pdf_directory_path, audio_only=True)
        if video_path:
            audio_path = os.path.join(pdf_directory_path, filename.rsplit('.', 1)[0] + '.wav')
            extract_audio_from_video(video_path, audio_path)
        else:
            continue  # Skip if the video download failed
    else:
        download_file(url, file_path)

# # Transcribe all the video and audio file present in the folder
for filename in os.listdir(pdf_directory_path):
    # file_path = os.path.join(pdf_directory_path, filename)
    if filename.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.mkv', '.avi', '.mov')):
        # Process audio and video files
        if filename.endswith(('.mp4', '.mkv', '.avi', '.mov')):
            audio_path = os.path.join(pdf_directory_path, filename.rsplit('.', 1)[0] + '.wav')
            extract_audio_from_video(os.path.join(pdf_directory_path, filename), audio_path)
        else:
            audio_path = os.path.join(pdf_directory_path, filename)

# #     # Save the transcription as PDF in the pdf folder
# #     # Transcribe audio, assuming non-English content might be present
    # Transcribe audio and save as text file
        transcription = transcribe_audio(audio_path)
        transcription_file_path = os.path.join(pdf_directory_path, f"{os.path.splitext(filename)[0]}_transcript.txt")
        save_text_as_file(transcription, transcription_file_path)
    # pdf_transcript_path = os.path.join(pdf_directory_path, f"{os.path.splitext(filename)[0]}_transcript.pdf")
    # # save_text_as_pdf(transcription, pdf_transcript_path)

# Iterate through all PDF files in the directory
for filename in os.listdir(pdf_directory_path):
    if filename.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.mkv', '.avi', '.mov')):
        continue
    elif filename in ['urls.txt' , 'url.txt' ]:
        continue
    elif filename.endswith(".pdf") or filename.endswith(".txt"):
        file_path = os.path.join(pdf_directory_path, filename)
        
        # Initialize an empty string to accumulate text from the current file
        file_text = ""
        
        if filename.endswith(".pdf"):
            # Open and read the PDF file
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract all text from the PDF
                for page_num in range(len(pdf_reader.pages)):
                    page_text = pdf_reader.pages[page_num].extract_text()
                    file_text += page_text.lower() + " "
        else:
            # Open and read the text file
            with open(file_path, 'r', encoding='utf-8') as text_file:
                file_text = text_file.read().lower()
        
        # Split the combined text into smaller chunks
        text_chunks = split_text(file_text)

        # Initialize a set to collect classes for the current file
        file_classes = set()
        file_summary = ""

        # Process each chunk separately
        for chunk in text_chunks:
            # Make the request to the OpenAI API for summary
            summary_response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {"role": "system", "content": "You are an agricultural expert. Summarize the provided text."},
                    {"role": "user", "content": f"Summarize the following text: {chunk}"}
                ]
            )

            # Extract and store the summary
            file_summary += summary_response.choices[0].message.content + "\n"

        # Write the individual summary to a file for classification
        summary_file_path = os.path.join(pdf_directory_path, f"{os.path.splitext(filename)[0]}_summary.txt")
        with open(summary_file_path, "w") as summary_file:
            summary_file.write(file_summary)

        # Append the summary to the cumulative summary list
        summaries.append(f"{filename}:\n{file_summary}\n")

        # Read the summary for classification
        with open(summary_file_path, "r") as summary_file:
            summary_text = summary_file.read()

        # Make the request to the OpenAI API for classification
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

        # Make the request to the OpenAI API
        classification_response = client.chat.completions.create(
                 model="gpt-3.5-turbo-0125",
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
        # Extract and process the response
        result = classification_response.choices[0].message.content.strip()
        result_classes = [cls.strip() for cls in result.split(",") if cls.strip()]
            
# Remove 'none' if any other class is present
        if len(result_classes) > 1 and 'none' in result_classes:
            result_classes.remove('none')
        
        file_classes.update(result_classes)

        # Store the classes identified for the current file
        all_classes[filename] = file_classes

        # Delete the individual summary file
        # os.remove(summary_file_path)

# Write the summaries to a new file
summaries_file_path = os.path.join(pdf_directory_path, "summaries.txt")
with open(summaries_file_path, "w") as summaries_file:
    summaries_file.write("\n".join(summaries))

# Read the summaries from the file and generate a cumulative summary
with open(summaries_file_path, "r") as summaries_file:
    summaries_text = summaries_file.read()


cumulative_summary_response = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=[
        {"role": "system", "content": "You are an agricultural expert. Summarize the provided text."},
        {"role": "user", "content": f"Generate a cumulative summary for the following summaries:\n\n{summaries_text}"}
    ],
    max_tokens= 255
)

# Extract and print the cumulative summary
cumulative_summary = cumulative_summary_response.choices[0].message.content
# Print the final results
print("\nClasses identified from all PDFs:")
for filename, classes in all_classes.items():
    print(f"{filename}: {', '.join(classes)}")
print("Cumulative Summary:")
print(cumulative_summary)
# Remove the summaries file
# os.remove(summaries_file_path)

   