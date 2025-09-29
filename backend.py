from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import google.generativeai as genai
import json
import datetime
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import tempfile
import base64

app = Flask(__name__)
CORS(app)  # Allow React frontend to call this API

# Configure Gemini API
genai.configure(api_key="AIzaSyChVzmf5YmhlEo8Z8ru4y4Dv7d40n7KCVE")  # Replace with your API key
model = genai.GenerativeModel('gemini-2.0-flash')

# Conversation history (simulates Redis storage)
conversation_history = []

# Sample farmer profile data
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

# Sample market data
SAMPLE_MARKET_DATA = {
    "rice": {"price": "₹2,100/quintal", "demand": "High", "trend": "Rising"},
    "cotton": {"price": "₹5,800/quintal", "demand": "Moderate", "trend": "Stable"},
    "groundnut": {"price": "₹5,200/quintal", "demand": "High", "trend": "Rising"}
}

# Sample weather data
SAMPLE_WEATHER = {
    "current": "Partly cloudy, 28°C",
    "forecast": "Rain expected in 3-4 days, 15mm precipitation",
    "advisory": "Good time for land preparation"
}

# Sample pest/disease alerts
SAMPLE_PEST_ALERTS = {
    "rice": "Brown Plant Hopper outbreak reported in nearby districts",
    "cotton": "Bollworm activity moderate, monitor closely"
}

# Sample government schemes
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

def get_system_prompt():
    """Generate system prompt with farmer profile and context"""
    return f"""You are an expert farmer advisory AI assistant specializing in Indian agriculture. You can understand queries in Malayalam written in Malayalam letters.

FARMER PROFILE:
- Name: {SAMPLE_FARMER_PROFILE['name']}
- Location: {SAMPLE_FARMER_PROFILE['location']}
- Farm Size: {SAMPLE_FARMER_PROFILE['farm_size']}
- Crops: {', '.join(SAMPLE_FARMER_PROFILE['crops'])}
- Soil Type: {SAMPLE_FARMER_PROFILE['soil_type']}
- Irrigation: {SAMPLE_FARMER_PROFILE['irrigation']}
- Last Yields: {SAMPLE_FARMER_PROFILE['last_yield']}

CURRENT CONDITIONS:
- Weather: {SAMPLE_WEATHER['current']}
- Forecast: {SAMPLE_WEATHER['forecast']}
- Weather Advisory: {SAMPLE_WEATHER['advisory']}

MARKET PRICES (Current):
{json.dumps(SAMPLE_MARKET_DATA, indent=2)}

PEST/DISEASE ALERTS:
{json.dumps(SAMPLE_PEST_ALERTS, indent=2)}

AVAILABLE SCHEMES:
{json.dumps(SAMPLE_SCHEMES, indent=2)}

CRITICAL RESPONSE INSTRUCTIONS:
1. ALWAYS respond in Malayalam letters 
2. Keep responses SHORT - maximum 1-2 sentences
3. Be direct and practical
4. Use simple Malayalam words 
5. Give specific actionable advice
6. Include prices/numbers when relevant

EXAMPLE RESPONSE STYLE:
Query: "അരിയുടെ വില എത്രയനു?"
Good Response: "അരിയുടെ വില കിലോയ്ക്ക് 200 രൂപയാണ്."

Bad Response: Long detailed explanations in English

Remember: SHORT, PRACTICAL, MALAYALAM LETTERS ONLY!
"""

def classify_intent(query):
    """Multilingual intent classification based on keywords"""
    query_lower = query.lower()
    
    # Market-related keywords (English, Hindi, Malayalam, Telugu, Tamil)
    market_keywords = [
        'വില', 'വിപണി', 'മാർക്കറ്റ്', 'വിൽക്കുക', 'പണം', 'റേറ്റ്',
    ]
    
    # Pest/Disease keywords
    pest_keywords = [
        'കീടം', 'രോഗം', 'പ്രാണി', 'സ്പ്രേ', 'മരുന്ന്',
    ]
    
    # Irrigation keywords
    irrigation_keywords = [
        'വെള്ളം', 'നനയ്ക്കൽ', 'ജലസേചനം',
    ]
    
    # Government schemes keywords
    scheme_keywords = [
        'പദ്ധതി', 'സബ്‌സിഡി', 'സർക്കാർ', 'വായ്പ',
    ]
    
    # Weather keywords
    weather_keywords = [
        'കാലാവസ്ഥ', 'മഴ', 'താപനില',
    ]
    
    if any(word in query_lower for word in market_keywords):
        return 'market'
    elif any(word in query_lower for word in pest_keywords):
        return 'pest_disease'
    elif any(word in query_lower for word in irrigation_keywords):
        return 'irrigation'
    elif any(word in query_lower for word in scheme_keywords):
        return 'schemes'
    elif any(word in query_lower for word in weather_keywords):
        return 'weather'
    else:
        return 'general_agronomy'

def get_farmer_advice(query):
    """Generate advice for farmer query using Gemini with conversation context"""
    try:
        # Classify intent
        intent = classify_intent(query)
        
        # Build conversation context
        context = ""
        if conversation_history:
            context = "\n\nPREVIOUS CONVERSATION:\n"
            for entry in conversation_history[-5:]:  # Last 5 exchanges for context
                context += f"Farmer: {entry['query']}\n"
                context += f"Assistant: {entry['response']}\n\n"
        
        # Prepare the full prompt with context
        system_prompt = get_system_prompt()
        full_prompt = f"{system_prompt}{context}\nFarmer Query: {query}\nIntent Category: {intent}\n\nProvide helpful advice:"
        
        # Generate response using Gemini
        response = model.generate_content(full_prompt)
        
        # Store in conversation history
        conversation_history.append({
            'query': query,
            'response': response.text,
            'intent': intent,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return {
            'response': response.text,
            'intent': intent,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'context_used': len(conversation_history) > 1
        }
        
    except Exception as e:
        return {
            'response': f'Sorry, I encountered an error: {str(e)}. Please check your API key and try again.',
            'intent': 'error',
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'context_used': False
        }

def speak_malayalam(text):
    """Convert Malayalam text to speech and return audio file path."""
    language = 'ml'
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"Error in TTS: {e}")
        return None

def translate_malayalam_to_english(malayalam_text):
    """Translate Malayalam text to English"""
    try:
        translated = GoogleTranslator(source='ml', target='en').translate(malayalam_text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return None

# ============== API ROUTES ==============

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests from frontend"""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'error': 'No query provided'
            }), 400
        
        # Get advice from Gemini
        result = get_farmer_advice(query)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'response': 'Sorry, something went wrong. Please try again.'
        }), 500

@app.route('/api/chat-with-audio', methods=['POST'])
@app.route('/api/chat-with-audio', methods=['POST'])
def chat_with_audio():
    """Handle chat requests and return both text and audio response"""
    try:
        data = request.json
        query = data.get('query', '')

        if not query:
            return jsonify({'error': 'No query provided'}), 400

        # Get advice from Gemini
        result = get_farmer_advice(query)

        # Generate audio for the response
        audio_path = speak_malayalam(result['response'])
        print(audio_path)
        if audio_path:
            # Extract only the file name (not the full path)
            audio_filename = os.path.basename(audio_path)

            # If you still want to keep the audio file on disk, DON'T delete it yet
            # os.remove(audio_path)  # remove only if you don't want to keep it

            # Add the filename to the response
            result['audio_file'] = audio_filename

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'response': 'Sorry, something went wrong. Please try again.'
        }), 500
    """Handle chat requests and return both text and audio response"""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'error': 'No query provided'
            }), 400
        
        # Get advice from Gemini
        result = get_farmer_advice(query)
        
        # Generate audio for the response
        audio_path = speak_malayalam(result['response'])
        
        if audio_path:
            # Read audio file and encode as base64
            with open(audio_path, 'rb') as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            
            # Clean up temp file
            #os.remove(audio_path)
            
            result['audio'] = audio_data
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'response': 'Sorry, something went wrong. Please try again.'
        }), 500

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """Convert speech audio to text (Malayalam)"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        
        # Save temporarily
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        audio_file.save(temp_audio.name)
        
        # Recognize speech
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_audio.name) as source:
            audio_data = recognizer.record(source)
            malayalam_text = recognizer.recognize_google(audio_data, language="ml-IN")
        
        # Translate to English
        english_text = translate_malayalam_to_english(malayalam_text)
        
        # Clean up
        os.remove(temp_audio.name)
        
        return jsonify({
            'malayalam_text': malayalam_text,
            'english_text': english_text,
            'success': True
        })
    
    except sr.UnknownValueError:
        return jsonify({
            'error': 'Could not understand the audio',
            'success': False
        }), 400
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to Malayalam speech"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                'error': 'No text provided'
            }), 400
        
        # Generate audio
        audio_path = speak_malayalam(text)
        
        if audio_path:
            # Read and encode audio
            with open(audio_path, 'rb') as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            
            # Clean up
            os.remove(audio_path)
            
            return jsonify({
                'audio': audio_data,
                'success': True
            })
        else:
            return jsonify({
                'error': 'Failed to generate audio',
                'success': False
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/translate', methods=['POST'])
def translate():
    """Translate Malayalam to English or vice versa"""
    try:
        data = request.json
        text = data.get('text', '')
        source_lang = data.get('source', 'ml')
        target_lang = data.get('target', 'en')
        
        if not text:
            return jsonify({
                'error': 'No text provided'
            }), 400
        
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        
        return jsonify({
            'original': text,
            'translated': translated,
            'source_language': source_lang,
            'target_language': target_lang,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history"""
    return jsonify({
        'history': conversation_history,
        'total': len(conversation_history)
    })

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return jsonify({
        'message': 'Conversation history cleared',
        'success': True
    })

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Get farmer profile data"""
    return jsonify(SAMPLE_FARMER_PROFILE)

@app.route('/api/market', methods=['GET'])
def get_market_data():
    """Get current market prices"""
    return jsonify(SAMPLE_MARKET_DATA)

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Get weather information"""
    return jsonify(SAMPLE_WEATHER)

@app.route('/api/pest-alerts', methods=['GET'])
def get_pest_alerts():
    """Get pest/disease alerts"""
    return jsonify(SAMPLE_PEST_ALERTS)

@app.route('/api/schemes', methods=['GET'])
def get_schemes():
    """Get government schemes"""
    return jsonify(SAMPLE_SCHEMES)

@app.route('/api/help', methods=['GET'])
def get_help():
    """Get sample queries and help information"""
    help_data = {
        "market_queries": [
            "ariyude vila ethrayanu?",
            "paruthi crop vilkanam eppozhanu nallath?",
            "groundnut rate kooduvano?"
        ],
        "pest_disease_queries": [
            "paruthi vilayil keedam undu enthanu cheyyendathu?",
            "nellu vilayil rogam vannirikkunnu",
            "spray cheyyendathu evide kittum?"
        ],
        "irrigation_queries": [
            "vellam kodukkan eppozhanu nallath?",
            "bore well vellam kurayunnu",
            "drip irrigation nallatho?"
        ],
        "weather_queries": [
            "mazha eppozhanu varuka?",
            "kaalaavastha engane undu?"
        ],
        "government_schemes": [
            "government paddhati enthokke undu?",
            "subsidy engane kittum?"
        ]
    }
    return jsonify(help_data)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Farmer Advisory API with Speech is running',
        'features': [
            'Chat with AI advisor',
            'Speech-to-text (Malayalam)',
            'Text-to-speech (Malayalam)',
            'Translation (Malayalam-English)',
            'Market data',
            'Weather information',
            'Pest alerts',
            'Government schemes'
        ],
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# ============== MAIN ==============

if __name__ == '__main__':
    print("=" * 80)
    print("🌾 FARMER ADVISORY API SERVER WITH SPEECH SUPPORT")
    print("=" * 80)
    print("✅ Server starting on http://localhost:5000")
    print("✅ API Endpoints:")
    print("   POST /api/chat                - Send farmer queries (text)")
    print("   POST /api/chat-with-audio     - Send queries and get audio response")
    print("   POST /api/speech-to-text      - Convert speech to text")
    print("   POST /api/text-to-speech      - Convert text to speech")
    print("   POST /api/translate           - Translate text")
    print("   GET  /api/history             - Get conversation history")
    print("   POST /api/clear               - Clear conversation history")
    print("   GET  /api/profile             - Get farmer profile")
    print("   GET  /api/market              - Get market data")
    print("   GET  /api/weather             - Get weather info")
    print("   GET  /api/pest-alerts         - Get pest alerts")
    print("   GET  /api/schemes             - Get government schemes")
    print("   GET  /api/help                - Get sample queries")
    print("   GET  /health                  - Health check")
    print("=" * 80)
    print("📝 Required packages:")
    print("   pip install flask flask-cors google-generativeai")
    print("   pip install SpeechRecognition deep-translator gTTS")
    print("   pip install pyaudio  # For microphone support (optional)")
    print("=" * 80)
    print("🎤 Features:")
    print("   ✓ Malayalam speech recognition")
    print("   ✓ Text-to-speech in Malayalam")
    print("   ✓ Malayalam-English translation")
    print("   ✓ Context-aware conversations")
    print("   ✓ Multi-intent classification")
    print("=" * 80)
    
    app.run(debug=True, port=5000, host='0.0.0.0')