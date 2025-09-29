from flask import Flask, request, jsonify, send_from_directory
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
from urllib.parse import urlparse

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
    return f"""You are an expert farmer advisory AI assistant specializing in Indian agriculture. You MUST respond in Malayalam script only.

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

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. ALWAYS respond in Malayalam script (മലയാളം) - NEVER in English or Manglish
2. Keep responses SHORT - exactly 2-3 sentences maximum
3. Be DIRECT and give ACTIONABLE advice
4. Use simple Malayalam words that farmers understand
5. Include specific numbers, prices, or timings when relevant

EXAMPLE RESPONSES FOR DIFFERENT INTENTS:

MARKET/PRICE QUERIES:
Query: "അരിയുടെ വില എത്രയാണ്?"
Response: "ഇപ്പോൾ അരിയുടെ വില ക്വിന്റലിന് ₹2,100 ആണ്. ആവശ്യം കൂടുതലാണ്, വില കൂടാൻ സാധ്യതയുണ്ട്."

Query: "പരുത്തി എപ്പോൾ വിൽക്കണം?"
Response: "പരുത്തിയുടെ വില ക്വിന്റലിന് ₹5,800 ആണ്. വില സ്ഥിരതയുള്ളതിനാൽ ഇപ്പോൾ വിൽക്കാം."

PEST/DISEASE QUERIES:
Query: "നെല്ലിൽ കീടം വന്നിട്ടുണ്ട്"
Response: "ബ്രൗൺ പ്ലാന്റ് ഹോപ്പർ ആണോ? അടുത്ത ജില്ലകളിൽ പടരുന്നുണ്ട്. ഉടൻ കീടനാശിനി തളിക്കുക, കൃഷി ഓഫീസിൽ നിന്ന് മരുന്ന് വാങ്ങൂ."

Query: "പരുത്തിയിൽ പുഴു ഉണ്ട്"
Response: "ബോൾവേം ആണോ? ഇപ്പോൾ മിതമായ തോതിൽ ഉണ്ട്. ദിവസവും പരിശോധിക്കുക, ആവശ്യമെങ്കിൽ സ്പ്രേ ചെയ്യുക."

IRRIGATION/WATER QUERIES:
Query: "എപ്പോൾ വെള്ളം കൊടുക്കണം?"
Response: "3-4 ദിവസത്തിനകം മഴ പ്രതീക്ഷിക്കുന്നു, 15mm. ഇപ്പോൾ ഭൂമി ഒരുക്കാൻ നല്ല സമയമാണ്, മഴയ്ക്ക് ശേഷം നടീൽ നടത്താം."

Query: "ബോർവെൽ വെള്ളം കുറവാണ്"
Response: "കനാൽ വെള്ളവും ഉപയോഗിക്കുക. ഡ്രിപ്പ് ഇറിഗേഷൻ സംവിധാനം സ്ഥാപിച്ചാൽ വെള്ളം 40% ലാഭിക്കാം."

GOVERNMENT SCHEME QUERIES:
Query: "സർക്കാർ പദ്ധതികൾ എന്തൊക്കെയാണ്?"
Response: "PM-KISAN പദ്ധതിയിൽ വർഷം ₹6,000 കിട്ടും. വിള ഇൻഷുറൻസിൽ 50% സബ്‌സിഡി ഉണ്ട്, ഭൂരേഖയുള്ളവർക്ക് അപേക്ഷിക്കാം."

WEATHER QUERIES:
Query: "കാലാവസ്ഥ എങ്ങനെയാണ്?"
Response: "ഇന്ന് ഭാഗികമായി മേഘാവൃതം, 28°C. 3-4 ദിവസത്തിനകം മഴ പ്രതീക്ഷിക്കുന്നു, നിലമൊരുക്കാൻ നല്ല സമയം."

GENERAL FARMING QUERIES:
Query: "നെല്ല് കൃഷി എങ്ങനെ തുടങ്ങണം?"
Response: "ആദ്യം നിലം ഉഴുതുനിരത്തുക. മഴ വന്നതിനുശേഷം നടീൽ ചെയ്യുക, നിങ്ങളുടെ ചുവന്ന മണ്ണിന് നെല്ല് നല്ലതാണ്."

Query: "എന്റെ വിള എങ്ങനെ ഉപേക്ഷിക്കണം?" or "വിള നശിപ്പിക്കണോ?"
Response: "വിള ഉപേക്ഷിക്കരുത്! പ്രശ്നം എന്താണെന്ന് പറയൂ - കീടം, വെള്ളക്കുറവ്, അല്ലെങ്കിൽ വിള നഷ്ടം? ഞങ്ങൾ പരിഹാരം കണ്ടെത്താം."

Query: "കൃഷി നഷ്ടമായി എന്ത് ചെയ്യും?"
Response: "വിള ഇൻഷുറൻസ് എടുത്തിട്ടുണ്ടോ? ഉണ്ടെങ്കിൽ നഷ്ടപരിഹാരം കിട്ടും. അടുത്ത സീസണിൽ മറ്റൊരു വിള പരീക്ഷിക്കാം."

REMEMBER:
- SHORT answers (2-3 sentences)
- Malayalam script ONLY
- Practical, actionable advice
- Include numbers/prices when relevant
- Never discourage farmers - always give solutions!
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
        return None

def extract_text_from_url(url):
    """Extracts text content from a given URL"""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error extracting text: {str(e)}")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------------
# API Endpoints
# -------------------------

@app.route("/api/farmer_to_response", methods=["POST"])
def farmer_to_response():
    """
    Handles audio input OR text query
    - converts audio to text
    - gets Gemini response
    - returns response + audio file URL
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
        
        if audio_filename:
            result['audio_url'] = f"http://localhost:5000/audio/{audio_filename}"

        return jsonify(result)

    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand the audio"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/url_to_response", methods=["POST"])
def url_to_response():
    """
    Accepts a URL, extracts text, sends to LLM with context,
    generates response and audio file
    
    Request body (JSON):
    {
        "url": "https://example.com/article"
    }
    """
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Extract text from URL
        extracted_text = extract_text_from_url(url)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            return jsonify({"error": "Could not extract meaningful text from URL"}), 400
        
        # Create query context
        query_context = f"ഈ ഉള്ളടക്കം അടിസ്ഥാനമാക്കി കൃഷി ഉപദേശം നൽകുക: {extracted_text[:2000]}"
        
        # Get Gemini advice
        result = get_farmer_advice(query_context)
        
        result['extracted_text'] = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
        result['source_url'] = url
        
        # Generate Malayalam audio
        audio_filename = text_to_malayalam_audio(result['response'])
        result['audio_file'] = audio_filename
        
        if audio_filename:
            result['audio_url'] = f"http://localhost:5000/audio/{audio_filename}"
        
        return jsonify(result)
    
    except Exception as e:
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