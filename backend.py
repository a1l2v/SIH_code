from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
from googletrans import Translator
import datetime
import tempfile
import os
import json

app = Flask(__name__)

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
    "language": "Telugu",
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
    return f"""You are an expert farmer advisory AI assistant specializing in Indian agriculture. Respond in Malayalam letters.

FARMER PROFILE:
- Name: {SAMPLE_FARMER_PROFILE['name']}
- Location: {SAMPLE_FARMER_PROFILE['location']}
- Farm Size: {SAMPLE_FARMER_PROFILE['farm_size']}
- Crops: {', '.join(SAMPLE_FARMER_PROFILE['crops'])}
- Soil Type: {SAMPLE_FARMER_PROFILE['soil_type']}
- Irrigation: {SAMPLE_FARMER_PROFILE['irrigation']}

CURRENT CONDITIONS:
- Weather: {SAMPLE_WEATHER['current']}
- Forecast: {SAMPLE_WEATHER['forecast']}
- Advisory: {SAMPLE_WEATHER['advisory']}

MARKET PRICES:
{json.dumps(SAMPLE_MARKET_DATA, indent=2)}

PEST ALERTS:
{json.dumps(SAMPLE_PEST_ALERTS, indent=2)}

SCHEMES:
{json.dumps(SAMPLE_SCHEMES, indent=2)}

CRITICAL RESPONSE INSTRUCTIONS:
1. Respond in Malayalam letters only
2. Keep it short (3–4 sentences)
3. Simple words, practical advice
"""

def classify_intent(query):
    q = query.lower()
    if any(k in q for k in ['വില','price','market','വിപണി']):
        return 'market'
    elif any(k in q for k in ['കീടം','pest','disease','spray']):
        return 'pest_disease'
    elif any(k in q for k in ['വെള്ളം','irrigation','water']):
        return 'irrigation'
    elif any(k in q for k in ['പദ്ധതി','scheme','subsidy']):
        return 'schemes'
    elif any(k in q for k in ['മഴ','weather','കാലാവസ്ഥ']):
        return 'weather'
    return 'general_agronomy'

def get_farmer_advice(query):
    intent = classify_intent(query)
    prompt = f"{get_system_prompt()}\n\nFarmer Query: {query}\nIntent: {intent}\n\nProvide helpful advice:"
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
        return filename  # return only filename
    except Exception as e:
        print("TTS Error:", e)
        return None
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# -------------------------
# API Endpoint
# -------------------------

@app.route("/api/farmer_to_response", methods=["POST"])
def farmer_to_response():
    """
    Handles:
    - audio input OR text query
    - converts audio to text
    - gets Gemini response
    - returns response + audio file name
    """
    try:
        query_text = None

        # If audio provided
        if 'audio' in request.files:
            audio_file = request.files['audio']
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            audio_file.save(temp_audio.name)

            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_audio.name) as source:
                audio_data = recognizer.record(source)
                query_text = recognizer.recognize_google(audio_data, language="ml-IN")

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

        return jsonify(result)

    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand the audio"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to serve audio files
@app.route("/audio/<filename>")
def get_audio(filename):
    audio_dir = os.path.join(os.getcwd(), "static", "audio")
    return send_from_directory(audio_dir, filename)

@app.route("/upload-file", methods=["POST"])

# Serve uploaded files
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# Upload MP3 file
@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".mp3"):
        return jsonify({"error": "Only MP3 files are allowed"}), 400

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
