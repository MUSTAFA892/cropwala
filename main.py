from flask import Flask, render_template, request, jsonify, send_from_directory
from google import genai
from dotenv import load_dotenv
import os
import json
import random
from datetime import datetime
import logging
import base64
from werkzeug.utils import secure_filename
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Gemini API key
API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client

client = genai.Client(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# System prompt for the chatbot
system_prompt = """
You are FarmHelper, a friendly, expert virtual farming assistant.
You know everything about agriculture: crop care, fertilizers, NPK values, water needs, pests, soil health, and weather impact.
Respond in the language the user speaks.
Keep your responses structured in short bullet points for easy reading (but not always).
Begin your messages with a friendly farmer emoji 👨‍🌾 to set the tone.
Tailor your advice to the user's specific growing zone and climate when available.
Provide practical, actionable advice that farmers can implement immediately.
For pest issues, always suggest both organic and conventional solutions.
For soil health questions, emphasize sustainable practices.
If the user sends an image, analyze it for plant health, disease, or pest issues.
If uncertain about specific details, acknowledge limitations but provide general best practices.
"""

# Initialize Flask app
app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Store conversation history
conversation_history = {}

# Mock database of crop information
crop_database = {
    "tomatoes": {
        "water_needs": "moderate",
        "sunlight": "full sun",
        "soil_ph": "6.0-6.8",
        "spacing": "24-36 inches",
        "common_pests": ["aphids", "hornworms", "whiteflies"],
        "growing_season": "summer",
        "days_to_maturity": "60-85 days"
    },
    "corn": {
        "water_needs": "high",
        "sunlight": "full sun",
        "soil_ph": "5.8-7.0",
        "spacing": "8-12 inches",
        "common_pests": ["corn earworms", "cutworms", "aphids"],
        "growing_season": "summer",
        "days_to_maturity": "60-100 days"
    },
    "lettuce": {
        "water_needs": "moderate",
        "sunlight": "partial shade",
        "soil_ph": "6.0-7.0",
        "spacing": "8-12 inches",
        "common_pests": ["aphids", "slugs", "snails"],
        "growing_season": "spring/fall",
        "days_to_maturity": "45-55 days"
    },
    "carrots": {
        "water_needs": "moderate",
        "sunlight": "full sun",
        "soil_ph": "6.0-6.8",
        "spacing": "2-3 inches",
        "common_pests": ["carrot flies", "nematodes"],
        "growing_season": "spring/fall",
        "days_to_maturity": "70-80 days"
    }
}

# Mock weather data
weather_data = {
    "New York": {"temp": "18°C", "conditions": "Partly Cloudy", "humidity": "65%"},
    "California": {"temp": "24°C", "conditions": "Sunny", "humidity": "45%"},
    "Texas": {"temp": "30°C", "conditions": "Clear", "humidity": "50%"},
    "Florida": {"temp": "26°C", "conditions": "Thunderstorms", "humidity": "80%"},
    "default": {"temp": "22°C", "conditions": "Sunny", "humidity": "60%"}
}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for serving the main page
@app.route("/")
def index():
    return render_template("index.html")

# Route for handling chat messages
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "default_session")
        user_location = data.get("location", "default")
        language = data.get("language", "en")

        logger.info(f"Received message from {session_id}: {user_message}")

        # Initialize conversation history for new session
        if session_id not in conversation_history:
            conversation_history[session_id] = [
                {"role": "system", "content": system_prompt}
            ]

        # Append user message to conversation history
        conversation_history[session_id].append({
            "role": "user",
            "content": user_message
        })

        # Prepare context with location and crop data
        context = f"User location: {user_location}\n"
        if user_location in weather_data:
            weather = weather_data[user_location]
            context += f"Current weather: {weather['temp']}, {weather['conditions']}, Humidity: {weather['humidity']}\n"
        else:
            weather = weather_data["default"]
            context += f"Default weather: {weather['temp']}, {weather['conditions']}, Humidity: {weather['humidity']}\n"

        # Check if message relates to a specific crop
        for crop in crop_database:
            if crop.lower() in user_message.lower():
                crop_info = crop_database[crop]
                context += f"Crop info for {crop}:\n"
                context += f"- Water needs: {crop_info['water_needs']}\n"
                context += f"- Sunlight: {crop_info['sunlight']}\n"
                context += f"- Soil pH: {crop_info['soil_ph']}\n"
                context += f"- Spacing: {crop_info['spacing']}\n"
                context += f"- Common pests: {', '.join(crop_info['common_pests'])}\n"
                context += f"- Growing season: {crop_info['growing_season']}\n"
                context += f"- Days to maturity: {crop_info['days_to_maturity']}\n"

        # Prepare the prompt with context
        full_prompt = context + "\nUser message: " + user_message

        # Generate response using Gemini API
        try:
            response = client.models.generate_content(full_prompt)
            bot_response = response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            bot_response = "👨‍🌾 Sorry, I'm having trouble processing your request. Please try again or ask something else."

        # Append bot response to conversation history
        conversation_history[session_id].append({
            "role": "assistant",
            "content": bot_response
        })

        # Keep only the last 10 messages to manage memory
        if len(conversation_history[session_id]) > 10:
            conversation_history[session_id] = conversation_history[session_id][-10:]

        # Generate suggestion chips
        suggestions = generate_suggestions(user_message)

        return jsonify({
            "response": bot_response,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "response": "👨‍🌾 An error occurred. Please try again.",
            "suggestions": [],
            "timestamp": datetime.now().isoformat()
        }), 500

# Helper function to generate suggestion chips
def generate_suggestions(user_message):
    all_suggestions = [
        "Best time to plant potatoes",
        "Natural pest control methods",
        "How to improve soil drainage",
        "Signs of overwatering",
        "Companion planting guide",
        "How to make compost",
        "Organic fertilizer options",
        "Crop rotation benefits",
        "When to harvest onions",
        "How to prevent tomato blight"
    ]
    
    # Filter suggestions based on message content
    related_suggestions = []
    user_message = user_message.lower()
    for suggestion in all_suggestions:
        if any(keyword in user_message for keyword in suggestion.lower().split()):
            related_suggestions.append(suggestion)
    
    # If no related suggestions, pick random ones
    if not related_suggestions:
        related_suggestions = random.sample(all_suggestions, min(3, len(all_suggestions)))
    else:
        # Limit to 3 suggestions
        related_suggestions = related_suggestions[:3]
    
    return related_suggestions

# Route for handling image uploads and analysis
@app.route("/analyze_image", methods=["POST"])
def analyze_image():
    try:
        if 'file' not in request.files:
            logger.error("No file provided in image analysis request")
            return jsonify({
                "response": "👨‍🌾 Please upload an image.",
                "analysis": []
            }), 400

        file = request.files['file']
        session_id = request.form.get("session_id", "default_session")
        user_location = request.form.get("location", "default")

        if file and allowed_file(file.filename):
            # Securely save the file
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            # Read image file for Gemini API
            with open(file_path, "rb") as image_file:
                image_data = image_file.read()

            # Prepare prompt for image analysis
            analysis_prompt = f"""
            Analyze this plant image for health, diseases, or pest issues.
            User location: {user_location}
            Provide a structured response with:
            - Plant identification
            - Health status
            - Identified issues (if any)
            - Recommendations (both organic and conventional)
            Respond in a friendly tone with the 👨‍🌾 emoji.
            """

            try:
                # Send image and prompt to Gemini API
                response = model.generate_content([analysis_prompt, {"mime_type": file.mimetype, "data": image_data}])
                analysis_result = response.text.strip()

                # Clean up the saved file
                os.remove(file_path)

                # Append to conversation history
                if session_id not in conversation_history:
                    conversation_history[session_id] = [
                        {"role": "system", "content": system_prompt}
                    ]
                conversation_history[session_id].append({
                    "role": "user",
                    "content": "Image upload for plant analysis"
                })
                conversation_history[session_id].append({
                    "role": "assistant",
                    "content": analysis_result
                })

                return jsonify({
                    "response": analysis_result,
                    "analysis": analysis_result.split("\n"),
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Gemini API error in image analysis: {str(e)}")
                os.remove(file_path)
                return jsonify({
                    "response": "👨‍🌾 Sorry, I couldn't analyze the image. Please try again.",
                    "analysis": [],
                    "timestamp": datetime.now().isoformat()
                }), 500

        else:
            logger.error("Invalid file type uploaded")
            return jsonify({
                "response": "👨‍🌾 Please upload a valid image file (PNG, JPG, JPEG).",
                "analysis": [],
                "timestamp": datetime.now().isoformat()
            }), 400

    except Exception as e:
        logger.error(f"Error in image analysis endpoint: {str(e)}")
        return jsonify({
            "response": "👨‍🌾 An error occurred. Please try again.",
            "analysis": [],
            "timestamp": datetime.now().isoformat()
        }), 500

# Route for handling location-based recommendations
@app.route("/location_recommendations", methods=["POST"])
def location_recommendations():
    try:
        data = request.json
        session_id = data.get("session_id", "default_session")
        user_location = data.get("location", "default")
        language = data.get("language", "en")

        logger.info(f"Location recommendation request from {session_id} for {user_location}")

        # Prepare context with weather data
        if user_location in weather_data:
            weather = weather_data[user_location]
        else:
            weather = weather_data["default"]
            user_location = "default"

        prompt = f"""
        Provide farming recommendations based on the following:
        - Location: {user_location}
        - Weather: {weather['temp']}, {weather['conditions']}, Humidity: {weather['humidity']}
        Suggest:
        - Suitable crops for the current season
        - Weather-specific farming tips
        - Potential pest or disease concerns
        Respond in a friendly tone with the 👨‍🌾 emoji.
        """

        try:
            response = model.generate_content(prompt)
            recommendations = response.text.strip()

            # Append to conversation history
            if session_id not in conversation_history:
                conversation_history[session_id] = [
                    {"role": "system", "content": system_prompt}
                ]
            conversation_history[session_id].append({
                "role": "user",
                "content": f"Location-based recommendations for {user_location}"
            })
            conversation_history[session_id].append({
                "role": "assistant",
                "content": recommendations
            })

            return jsonify({
                "response": recommendations,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Gemini API error in location recommendations: {str(e)}")
            return jsonify({
                "response": "👨‍🌾 Sorry, I couldn't generate recommendations. Please try again.",
                "timestamp": datetime.now()
            }), 500

    except Exception as e:
        logger.error(f"Error in location recommendations endpoint: {str(e)}")
        return jsonify({
            "response": "👨‍🌾 An error occurred. Please try again.",
            "timestamp": datetime.now().isoformat()
        }), 500

# Route for serving uploaded files (if needed)
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Main entry point
if __name__ == "__main__":
    app.run(debug=True)