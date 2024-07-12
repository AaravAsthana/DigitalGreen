# DigitalGreen
# Automatic Transcription and Classification of Agricultural Texts

This Python project automates the process of downloading files from URLs, transcribing audio files, summarizing PDF and text files, and classifying text into agricultural categories using OpenAI's APIs.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo

2. **Install dependencies:**
pip install -r requirements.txt

3. **Set up environment variables:**

Create a .env file in the root directory.
Add your OpenAI API key:
OPENAI_API_KEY=your_openai_api_key

## How It Works

1. Setup and Initialization
The script initializes necessary modules and loads environment variables using dotenv.
2. File Download and Preparation
Reads URLs from pdf/urls.txt and downloads files (PDF, audio, video) into the pdf/ directory.
YouTube videos are downloaded and converted to audio using yt_dlp and pydub.
3. Text Extraction and Transcription
PDF and text files are processed to extract text content.
Audio files (converted from videos) are transcribed using OpenAI's Whisper model.
4. Text Summarization
Each extracted text is split into manageable chunks and summarized using OpenAI's GPT-3.5 model.
Summaries are stored in <filename>_summary.txt files.
5. Text Classification
Summaries are classified into agricultural categories (paddy, wheat, ragi, garlic, etc.) using GPT-3.5.
Results are stored in memory and printed at the end.
6. Cumulative Summary Generation
All individual summaries are combined and processed to generate a comprehensive cumulative summary using GPT-3.5.
7. Output
The script outputs:
Classification results for each file.
Cumulative summary of all files processed.

## File Structure

pdf/
│
├── urls.txt            # File containing URLs for download
├── <filename>.pdf      # PDF files for transcription
├── <filename>.txt      # Text files for transcription
├── <filename>_summary.txt  # Summaries of each file
├── summaries.txt       # Cumulative summaries of all files
└── <audio/video files> # Downloaded and processed audio/video files

## Usage

1. Prepare URLs:
   Create a file named urls.txt in the pdf/ directory.
   Add URLs to PDF, audio, or video files you want to process, one per line.

2. Run the Script:
   python your_script.py

3. Notes:
   Ensure Python version compatibility (e.g., Python 3.x).
   Adjust permissions and paths as per your system requirements.
   For detailed functionality, refer to comments and function descriptions in your_script.py.

