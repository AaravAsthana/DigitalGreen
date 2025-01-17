# DigitalGreen
# Automatic Transcription and Classification of Agricultural Texts

This project is a Flask web application integrated with Celery for background task processing and Redis as the message broker. Docker is used to containerize the application and its dependencies. The application processes files from the local server, downloads additional files from URLs specified in a text file, transcribes audio, summarizes text, and classifies the summarized content using OpenAI's GPT model.


## Features

1.Download files from the server (local in this project).

2.Download additional files specified in a urls.txt file.

3.Extract audio from video files.

4.Transcribe audio files using OpenAI Whisper.

5.Summarize text files using OpenAI's GPT-3.5-turbo.

6.Classify summarized content into specific agricultural categories.

7.Provide endpoints to initiate the process and check the status of the tasks.

## Prerequisites

1. Python 3.10 or higher

2. Redis server (for Celery backend) running on local host

3. OpenAI API key

4. FFmpeg (for audio extraction)

5. Docker

6. Docker Compose


## Installation

1. Clone the repository:

   ```bash 
   git clone https://github.com/AaravAsthana/DigitalGreen.git
   cd flask-celery-file-processing
   ```
2. Create and activate a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```
3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```
4. Install and run Redis:

     Download Redis for Windows from [Redis Download Page.](https://github.com/microsoftarchive/redis/releases)
     
     Extract the archive and run ````redis-server.exe.````

5. Set up environment variables:

     Create a .env file in the project root directory and add the following variables:
      ````
      OPENAI_API_KEY=your_openai_api_key
      CELERY_BROKER_URL=redis://localhost:6379/0
      CELERY_RESULT_BACKEND=redis://localhost:6379/0
      ````

6. Install FFmpeg:

     Download and install FFmpeg from [FFmpeg Download Page](https://ffmpeg.org/download.html).
   
     Add FFmpeg to your system PATH.

## How It Works

1. Initiating the Process:

   Users upload multiple files through the /upload endpoint. The files are saved in the temp_uploads directory, and a Celery task is initiated to process these files asynchronously.

2. Downloading Files :

   The Celery task (process_files) starts by downloading the specified files from the local server(through Postman) to a local directory (./pdfs).

3. Downloading Additional Files from URLs:

   If a urls.txt file is present among the downloaded files, the application reads URLs from this file and downloads the corresponding files.
   For YouTube URLs, it downloads the audio using yt-dlp.
   For other URLs, it downloads the files directly using requests.

4. Extracting Audio from Video Files:

   The application checks the downloaded files for video files and extracts audio from them using pydub and FFmpeg.

5. Transcribing Audio Files:

   Audio files (including those extracted from videos) are transcribed using OpenAI Whisper. The transcriptions are saved as text files.

6. Processing Text Files:

   The application processes all text files, including the transcriptions and any other text or PDF files downloaded from S3 or URLs.
   For PDF files, it uses PyPDF2 to extract text from each page.

7. Summarizing Text:
   
   The extracted text is split into chunks to ensure it stays within the token limit for OpenAI API calls.
   Each chunk is summarized using OpenAI's GPT-3.5-turbo model.
   The summaries are concatenated to form a cumulative summary.

8. Classifying Summarized Text:

   The cumulative summary is classified into specific agricultural categories using OpenAI's GPT-3.5-turbo model.
   The application uses predefined criteria to determine which categories the summarized text falls into.

9. Returning Results:

   The Celery task collects all the classifications and the cumulative summary.
   The results are returned and can be retrieved by sending a GET request to the /task_status/<task_id> endpoint with the task ID received from the initial request.


## File Structure
````
Automatic classification and summarisation of agricultural texts/
├── temp_uploads/ # Directory for temporary file uploads
├── pdfs/ # Directory for storing processed files
├── app.py # Flask application
├── tasks.py # Celery tasks
├── celery_config.py # Celery configuration with Flask context
├── requirements.txt # Python dependencies
├── Dockerfile # Dockerfile for building the Flask and Celery images
├── docker-compose.yml # Docker Compose file for orchestrating services
└── README.md # Project documentation
````
## Usage

### Building and running the Docker Container

   ````
      docker-compose up --build
   ````
   This command builds the Docker images and starts the containers for the Flask app, Celery worker, and Redis server.

### Access the Application

   Open your browser and navigate to http://localhost:5000 to access the Flask application.

### Running the Application
   1. Start the Redis server:
   
      Ensure you have a Redis server running on localhost with the default port 6380.
      
   2. Start the Celery worker:
   
   
      ````
      celery -A tasks worker --pool=solo -l info
      ````
   3. Start the Flask application:
   
      ````
      python app.py
      ````

### API Endpoints
   1. Upload Files
   
      - Endpoint: /upload
        
      - Method: POST
   
      - Body: form-data
   
           - Key: files (multiple entries for each file you want to upload)
            
           - Value: Choose the files to upload
      
      Response :
      
         ````
            {
            "task_id":"<task_id>"
            }
         ````
     
   3. Check Task Status
   
      - Endpoint: /task_status/<task_id>
      
      - Method: GET
        
      Response :
      
      ````
                  {
                    "task_id": "<task_id>",
                    "task_status": "PENDING|STARTED|SUCCESS|FAILURE",
                    "task_result": {
                      "summary": "<cumulative_summary>",
                      "classes": {
                        "<filename>": "<classification>"
                      }
                    }
                  }
      ````
## Function Descriptions

- download_youtube_video(url, output_path, audio_only=False): Downloads a YouTube video using yt-dlp.
- download_audio_video_from_link(url, output_path): Downloads a file from a direct URL.
- extract_audio_from_video(video_path, audio_path): Extracts audio from a video file.
- transcribe_audio(audio_path, language="en"): Transcribes audio using OpenAI Whisper.
- save_text_as_file(text, file_path): Saves text to a file.
- split_text(text, max_tokens=1500): Splits text into chunks for processing.
- summarize_text(text): Summarizes text using OpenAI GPT-3.5-turbo.
- classify_text(summary_text): Classifies summarized text into agricultural categories.


## Environment Variables

The following environment variables are used in the docker-compose.yml file:

- FLASK_APP: Specifies the entry point for the Flask application (e.g., app.py).
- FLASK_RUN_HOST: Configures Flask to run on all network interfaces (0.0.0.0).
- CELERY_BROKER_URL: URL of the Redis broker used by Celery (e.g., redis://redis:6379).
- CELERY_RESULT_BACKEND: URL of the Redis backend used by Celery (e.g., redis://redis:6379).

## Dockerfile

The Dockerfile builds an image for both the Flask application and Celery worker with the following steps:

1. Use the official Python 3.10 slim image.
2. Set the working directory to /app.
3. Copy the application files into the container.
4. Install Python dependencies from requirements.txt.
5. Expose port 5000 for the Flask application.
6. Set environment variables for Flask.
7. Define the default command to run Flask.

## docker-compose.yml

The docker-compose.yml file defines three services:

- flask-app: The Flask web application.
- redis: The Redis server used as a message broker and result backend.
- celery-worker: The Celery worker for processing background tasks.

All services are connected to a custom network app-network for internal communication.

## Volumes

The docker-compose.yml file mounts the following volumes:

   - The current directory (.) is mounted to /app in both the Flask and Celery containers.
   - A local directory (./temp_uploads) is mounted to /app/temp_uploads for temporary file storage.

## Troubleshooting

- Ensure Docker and Docker Compose are installed and running.
- Check the logs for errors by running docker-compose logs or docker-compose logs <service-name>.
- Verify that the ports 5000 and 6380 are available and not in use by other applications.

## Example Workflow

1. User Request:

   User sends a POST request to /upload with the following body:
   ````json
   {
     "bucket_name": "your-s3-bucket-name",
     "file_keys": ["file1.pdf", "file2.mp4", "urls.txt"]
   }
   ````
2. File Download:

   The application downloads file1.pdf, file2.mp4, and urls.txt from the specified S3 bucket.

3. URL Processing:

   The application reads urls.txt and downloads additional files specified in it.

4. Audio Extraction and Transcription:

   The application extracts audio from file2.mp4 and other video files.
   The audio is transcribed using Whisper.

5. Text Summarization and Classification:

   The application summarizes the text from file1.pdf, transcriptions, and any other text files.
   The summarized text is classified into agricultural categories.

6. Result Retrieval:

   User sends a GET request to /task_status/<task_id> to retrieve the task status and results.
   The application returns the cumulative summary and classifications.


## Notes
+ The urls.txt file should contain one URL per line.
+ This application requires an active internet connection to interact with the OpenAI API.
