from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
from googletrans import Translator
import datetime
import tempfile
import os
import json
import requests
from bs4 import BeautifulSoup
from pydub import AudioSegment
from urllib.parse import urlparse
import io
import traceback

app = Flask(__name__)

CORS(app)

# -------------------------
# Configure Gemini API
# -------------------------
genai.configure(api_key="AIzaSyChVzmf5YmhlEo8Z8ru4y4Dv7d40n7KCVE")
model = genai.GenerativeModel("gemini-2.0-flash")

# -------------------------
# Sample Data
# -------------------------
SAMPLE_FARMER_PROFILE = {
    "name": "Ramesh Kumar",
    "location": "Kurnool, Andhra Pradesh",
    "farm_size": "5 acres",
    "crops": ["Rice", "Cotton", "Groundnut"],
    "soil_type": "Red soil",
    "irrigation": "Bore well + Canal",
    "language": "Malayalam",
    "last_yield": {
        "rice": "4.2 tons/acre",
        "cotton": "12 quintals/acre"
    },
    "upcoming_season": "Kharif 2024",
    "weather_conditions": "Monsoon expected in 2 weeks"
}

SAMPLE_MARKET_DATA = {
    "rice": {"price": "₹2,100/quintal", "demand": "High", "trend": "Rising"},
    "cotton": {"price": "₹5,800/quintal", "demand": "Moderate", "trend": "Stable"},
    "groundnut": {"price": "₹5,200/quintal", "demand": "High", "trend": "Rising"}
}

SAMPLE_WEATHER = {
    "current": "Partly cloudy, 28°C",
    "forecast": "Rain expected in 3-4 days, 15mm precipitation",
    "advisory": "Good time for land preparation"
}

SAMPLE_PEST_ALERTS = {
    "rice": "Brown Plant Hopper outbreak reported in nearby districts",
    "cotton": "Bollworm activity moderate, monitor closely"
}

SAMPLE_SCHEMES = [
    {
        "name": "PM-KISAN",
        "benefit": "₹6,000/year direct cash transfer",
        "eligibility": "Small and marginal farmers"
    },
    {
        "name": "Crop Insurance",
        "benefit": "Premium subsidy up to 50%",
        "eligibility": "All farmers with valid land records"
    }
]

# -------------------------
# Helper Functions
# -------------------------
def get_system_prompt():
    return f"""You are a farmer advisory AI. Always respond in Malayalam script only.

Farmer: {SAMPLE_FARMER_PROFILE['name']}, {SAMPLE_FARMER_PROFILE['location']}
Crops: {', '.join(SAMPLE_FARMER_PROFILE['crops'])}

Rules:
1. ALWAYS respond in Malayalam script (മലയാളം)
2. Keep responses SHORT - 2-3 sentences maximum
3. Give ACTIONABLE advice
4. Use simple Malayalam words
5. Include numbers/prices when relevant
6. Never discourage farmers - always give solutions
7. If data unavailable, feel free to use common farming knowledge

Current Market Prices:
- Rice: ₹2,100/quintal
- Cotton: ₹5,800/quintal  
- Groundnut: ₹5,200/quintal

Pest Alerts:
- Rice: Brown Plant Hopper outbreak nearby
- Cotton: Bollworm moderate activity

Weather: {SAMPLE_WEATHER['forecast']}
"""

def classify_intent(query):
    """Enhanced multilingual intent classification"""
    q = query.lower()
    
    # Market/Price keywords
    if any(k in q for k in ['വില','price','market','വിപണി','വിൽക്ക','sell','rate','ധര','കിലോ','quintal','ക്വിന്റൽ']):
        return 'market'
    
    # Pest/Disease keywords
    elif any(k in q for k in ['കീടം','കീട','pest','disease','രോഗം','spray','തളിക്ക','പുഴു','insect','bug','fungus']):
        return 'pest_disease'
    
    # Irrigation/Water keywords
    elif any(k in q for k in ['വെള്ളം','water','irrigation','നീര്','drip','sprinkler','bore','well','canal']):
        return 'irrigation'
    
    # Government Scheme keywords
    elif any(k in q for k in ['പദ്ധതി','scheme','subsidy','സബ്സിഡി','government','സർക്കാർ','loan','insurance','ഇൻഷുറൻസ്']):
        return 'schemes'
    
    # Weather keywords
    elif any(k in q for k in ['മഴ','weather','കാലാവസ്ഥ','temperature','rain','forecast','climate']):
        return 'weather'
    
    # Crop failure / giving up keywords
    elif any(k in q for k in ['ഉപേക്ഷിക്ക','drop','give up','quit','നശിപ്പിക്ക','destroy','നഷ്ടം','loss','failed']):
        return 'crop_failure_support'
    
    # General farming
    else:
        return 'general_agronomy'

def get_farmer_advice(query):
    intent = classify_intent(query)
    prompt = f"{get_system_prompt()}\n\nFarmer Query: {query}\nIntent: {intent}\n\nProvide helpful advice in Malayalam:"
    response = model.generate_content(prompt)
    return {
        "response": response.text,
        "intent": intent,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def text_to_malayalam_audio(text):
    try:
        audio_dir = os.path.join(os.getcwd(), "static", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        filename = f"response_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(audio_dir, filename)
        tts = gTTS(text=text, lang='ml')
        tts.save(filepath)
        return filename
    except Exception as e:
        print("TTS Error:", e)
        traceback.print_exc()
        return None

def extract_text_from_url(url):
    """
    Downloads WebM from URL and converts it to text.
    Works with WebM input files.
    """
    try:
        # 1. Download WebM file
        response = requests.get(url, stream=True, timeout=20)
        response.raise_for_status()

        # Save to temporary WebM file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_webm:
            for chunk in response.iter_content(chunk_size=1024):
                tmp_webm.write(chunk)
            tmp_webm_path = tmp_webm.name

        # 2. Load WebM and convert to audio data for speech recognition
        audio = AudioSegment.from_file(tmp_webm_path, format="webm")
        
        # Export to a BytesIO buffer as WAV data (in-memory only)
        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        buffer.seek(0)

        # 3. Recognize speech directly from buffer
        recognizer = sr.Recognizer()
        with sr.AudioFile(buffer) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language='ml-IN')
            except:
                text = recognizer.recognize_google(audio_data, language='en-IN')

        # Clean up temporary WebM file
        os.remove(tmp_webm_path)
        
        print(f"Transcribed text: {text}")
        return text

    except sr.UnknownValueError:
        traceback.print_exc()
        return "Error: Could not understand audio"
    except sr.RequestError as e:
        traceback.print_exc()
        return f"Error: Speech recognition service error - {e}"
    except Exception as e:
        traceback.print_exc()
        return f"Error: {e}"

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------------
# API Endpoints
# -------------------------

@app.route("/api/farmer_to_response", methods=["POST"])
def farmer_to_response():
    """
    Handles audio input OR text query - WebM input, MP3 output
    """
    try:
        query_text = None

        # If audio provided
        if 'audio' in request.files:
            audio_file = request.files['audio']
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
            audio_file.save(temp_audio.name)

            # Load WebM and convert to buffer (in-memory)
            audio = AudioSegment.from_file(temp_audio.name, format="webm")
            buffer = io.BytesIO()
            audio.export(buffer, format="wav")
            buffer.seek(0)

            recognizer = sr.Recognizer()
            with sr.AudioFile(buffer) as source:
                audio_data = recognizer.record(source)
                try:
                    query_text = recognizer.recognize_google(audio_data, language="ml-IN")
                except:
                    query_text = recognizer.recognize_google(audio_data, language="en-IN")

            os.remove(temp_audio.name)

        # If text provided
        if not query_text:
            query_text = request.form.get('query') or request.json.get('query')

        if not query_text:
            return jsonify({"error": "No query provided"}), 400

        # Get Gemini advice
        result = get_farmer_advice(query_text)

        # Generate Malayalam speech
        audio_filename = text_to_malayalam_audio(result['response'])
        result['audio_file'] = audio_filename
        
        if audio_filename:
            result['audio_url'] = f"http://localhost:5000/audio/{audio_filename}"

        return jsonify(result)

    except sr.UnknownValueError:
        traceback.print_exc()
        return jsonify({"error": "Could not understand the audio"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/url_to_response", methods=["POST"])
def url_to_response():
    """
    Accepts a URL, extracts audio/text, sends to LLM with context,
    generates response and audio file
    
    Request body (JSON):
    {
        "url": "https://example.com/audio.mp3"
    }
    """
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Extract text from URL (audio transcription)
        extracted_text = extract_text_from_url(url)
        
        if not extracted_text or extracted_text.startswith("Error:"):
            return jsonify({"error": extracted_text or "Could not extract audio"}), 400
        
        if len(extracted_text.strip()) < 3:
            return jsonify({"error": "Could not extract meaningful text from audio"}), 400
        
        # Get Gemini advice based on transcribed query
        result = get_farmer_advice(extracted_text)
        
        result['transcribed_query'] = extracted_text
        result['source_url'] = url
        
        # Generate Malayalam audio
        audio_filename = text_to_malayalam_audio(result['response'])
        result['audio_file'] = audio_filename
        
        if audio_filename:
            result['audio_url'] = f"http://localhost:5000/audio/{audio_filename}"
        
        return jsonify(result)
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/process_local_audio", methods=["POST"])
def process_local_audio():
    """
    Process an already uploaded WebM file
    Request body: {"filename": "crop_what_time_growth.webm"}
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({"error": "No filename provided"}), 400
        
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # Load WebM directly
        audio = AudioSegment.from_file(file_path, format="webm")
        
        # Convert to buffer for speech recognition (in-memory)
        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        buffer.seek(0)
        
        # Speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(buffer) as source:
            audio_data = recognizer.record(source)
            try:
                query_text = recognizer.recognize_google(audio_data, language='ml-IN')
            except:
                query_text = recognizer.recognize_google(audio_data, language='en-IN')
        
        # Get Gemini advice
        result = get_farmer_advice(query_text)
        result['transcribed_query'] = query_text
        result['source_file'] = filename
        
        # Generate Malayalam audio
        audio_filename = text_to_malayalam_audio(result['response'])
        result['audio_file'] = audio_filename
        
        if audio_filename:
            result['audio_url'] = f"http://localhost:5000/audio/{audio_filename}"
        
        return jsonify(result)
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<filename>")
def get_audio(filename):
    audio_dir = os.path.join(os.getcwd(), "static", "audio")
    return send_from_directory(audio_dir, filename)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".webm"):
        return jsonify({"error": "Only WebM files are allowed"}), 400

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)

    url = f"http://localhost:5000/uploads/{file.filename}"
    return jsonify({
        "filename": file.filename,
        "url": url,
        "message": "File uploaded successfully!"
    })

if __name__ == "__main__":
    app.run(debug=True)