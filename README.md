### Farmer Chatbot 🌾

#### Overview
The Farmer Chatbot 🌱 is a web-based application crafted to support farmers with their agricultural needs. Powered by Flask and Google Generative AI, it delivers real-time guidance on crop management 🌽, pest control 🐞, soil health 🌍, and more. With an intuitive interface, it offers interactive features like suggestion chips 💡, image analysis for plant health 📸, and location-based recommendations tailored to your climate 📍. Supporting multiple languages 🌐 and customizable themes 🎨, it ensures an accessible and personalized experience. The chatbot empowers farmers with practical insights to boost crop yield and farm efficiency 🚜.

#### Setup and Running Instructions

1. **Clone the Repository** 📥:
   Clone the Farmer Chatbot repository to your local machine:
   ```bash
   git clone https://github.com/your-username/farmer-chatbot.git
   cd farmer-chatbot
   ```

2. **Set Up a Virtual Environment** 🛠️:
   Create and activate a virtual environment to isolate project dependencies:
   ```bash
   python -m venv venv
   ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies** 📦:
   Install the required Python packages listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables** 🔑:
   Copy the `.env.example` file to `.env` and add your credentials:
   ```bash
   cp .env.example .env
   ```

5. **Run the Application** 🚀:
   Start the Flask development server:
   ```bash
   python main.py
   ```
   Open a browser and navigate to `http://127.0.0.1:5000` to interact with the chatbot 🌻.