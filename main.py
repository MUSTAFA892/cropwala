from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Gemini API key
API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

# System prompt for the chatbot
system_prompt = """
You are a smart, multilingual virtual farming assistant.
You know everything about agriculture: crop care, fertilizers, NPK values, water needs, pests, soil health, and weather impact.
Respond in the language the user speaks.

Try to give response in points. and also keep it very short and simple so that the user gets the whole idea 

Note :- Dont give big paragraph
"""


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    full_prompt = f"{system_prompt}\n\nUser: {user_message}"

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt
    )

    reply = response.text.strip()
    return jsonify({"response": reply})

if __name__ == "__main__":
    app.run(debug=True)
