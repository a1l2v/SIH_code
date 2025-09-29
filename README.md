# Farmer Advisory System - Setup Guide

## Prerequisites

### 1. Install Python 3.8+
Download from: https://www.python.org/downloads/

### 2. Install ffmpeg (Required for audio processing)

#### Windows:
```bash
winget install ffmpeg
```
**After installation, restart your terminal/PowerShell**

Verify installation:
```bash
ffmpeg -version
```

#### macOS:
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Linux (CentOS/RHEL):
```bash
sudo yum install ffmpeg
```

---

## Installation Steps

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd SIH_code
```

### 2. Create virtual environment (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Edit `app.py` and add your Gemini API key:
```python
genai.configure(api_key="YOUR_API_KEY_HERE")
```

### 5. Create required directories
```bash
mkdir -p static/audio uploads
```

---

## Running the Application

### Start the Flask server:
```bash
python app.py
```

The server will start at: `http://localhost:5000`

---

## API Endpoints

### 1. Upload Audio File
```bash
POST /upload-audio
Content-Type: multipart/form-data
Body: file (MP3 only)
```

### 2. Process Local Audio
```bash
POST /api/process_local_audio
Content-Type: application/json
Body: {"filename": "audio.mp3"}
```

### 3. Process Audio from URL
```bash
POST /api/url_to_response
Content-Type: application/json
Body: {"url": "http://example.com/audio.mp3"}
```

### 4. Text/Audio Query
```bash
POST /api/farmer_to_response
Content-Type: multipart/form-data or application/json
Body: audio file or {"query": "text query"}
```

---

## Troubleshooting

### "Couldn't find ffmpeg or avconv"
- Ensure ffmpeg is installed and in your system PATH
- Restart your terminal after installation
- Test with: `ffmpeg -version`

### "Could not understand the audio"
- Ensure audio is clear and in Malayalam or English
- Check audio quality and format (MP3 only)

### "Module not found" errors
- Activate virtual environment
- Run: `pip install -r requirements.txt`

---

## Project Structure
```
SIH_code/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── static/
│   └── audio/         # Generated audio responses
├── uploads/           # Uploaded audio files
└── README.md          # This file
```

---

## Dependencies

See `requirements.txt` for full list. Key packages:
- Flask - Web framework
- google-generativeai - Gemini AI
- speech_recognition - Audio to text
- gtts - Text to speech
- pydub - Audio processing (requires ffmpeg)
- requests - HTTP requests
- beautifulsoup4 - Web scraping

---

## License
[Your License Here]

## Support
For issues, contact: [Your Contact Info]