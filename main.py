from flask import Flask, render_template, request, jsonify, send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv
import os
import logging
import uuid
from datetime import datetime
import random
from werkzeug.utils import secure_filename

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Gemini API key
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

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

        # Prepare context with location
        context = f"User location: {user_location}\nUser language: {language}\n"
        
        # Create prompt for Gemini API
        full_prompt = f"{system_prompt}\n\n{context}\nUser message: {user_message}"

        # Generate response using Gemini API
        try:
            response = model.generate_content(full_prompt)
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

        # Generate suggestion chips using Gemini
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

# Helper function to generate suggestion chips using Gemini instead of hardcoded values
def generate_suggestions(user_message):
    try:
        suggestion_prompt = f"""
        Based on this user message about farming: "{user_message}"
        Generate exactly 3 follow-up question suggestions related to farming, agriculture, or gardening.
        Each suggestion should be brief (under 7 words if possible) and practical.
        Format your response as a plain list of 3 items, one per line, no bullets or numbers.
        If the user message doesn't contain enough context, provide general farming-related suggestions.
        """
        
        response = model.generate_content(suggestion_prompt)
        suggestions_text = response.text.strip()
        
        # Split the response into individual suggestions
        suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
        
        # Ensure we have 3 suggestions at most
        suggestions = suggestions[:3]
        
        # If somehow we got no suggestions, use some defaults
        if not suggestions:
            suggestions = [
                "Best planting times",
                "Natural pest control",
                "Soil health tips"
            ]
            
        return suggestions
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return [
            "Best planting times",
            "Natural pest control",
            "Soil health tips"
        ]

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

        prompt = f"""
        Provide farming recommendations based on the following:
        - Location: {user_location}
        
        Consider typical weather patterns, soil conditions, and agricultural practices for this location.
        
        Suggest:
        - Suitable crops for the current season (it's currently {datetime.now().strftime('%B')}, so focus on seasonal crops)
        - Weather-specific farming tips relevant to this location
        - Potential pest or disease concerns for this region
        - Local agricultural best practices
        
        Respond in a friendly tone with the 👨‍🌾 emoji.
        Use {language} language for your response.
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
                "timestamp": datetime.now().isoformat()
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