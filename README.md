
---

## 🌾 CropWala: NPK & Crop Yield Prediction using ML

**CropWala** is a machine learning-powered project designed to help farmers by predicting the optimal **NPK (Nitrogen, Phosphorus, Potassium)** values for their soil and forecasting potential **crop yield** based on those values.

> ⚠️ This repo is currently in development stage. The core ML models are trained and ready — integration and deployment coming next!

---

### 📌 Project Goals

- 🧪 Predict ideal **NPK** values for a given soil and environmental context
- 🌽 Predict **crop yield** based on NPK values
- 📉 Help reduce overuse of fertilizers and increase sustainable farming
- 🔍 Provide insights using EDA and data visualization

---

### 📁 Current Project Structure

```
CropWala/
├── models/
│   ├── best_rf_model.pkl       # NPK prediction model
│   └── yield_model.pkl         # Yield prediction model
│
├── eda/
│   └── data_cleaning.ipynb     # Data cleaning & preprocessing steps
│
├── train/
│   ├── npk_model_training.ipynb    # Notebook to train and export NPK model
│   └── yield_model_training.ipynb  # Notebook to train and export yield model
│
└── README.md                   # You're here!
```

---

### 🧠 Machine Learning Models

#### 1️⃣ NPK Prediction
- **Input**: Temperature, moisture, rainfall, pH, carbon %, soil type, crop
- **Output**: Required N, P, K values
- **Model**: Random Forest Regressor (`best_rf_model.pkl`)

#### 2️⃣ Crop Yield Prediction
- **Input**: N, P, K values
- **Output**: Estimated crop yield
- **Model**: Regression model (Tuned for performance)

---

### ✅ What’s Working

- ✔️ Cleaned and preprocessed datasets
- ✔️ Trained and saved both ML models (`.pkl`)
- ✔️ Reproducible training notebooks

---

### 🛠️ What's Coming Next

- [ ] Flask app for user input and predictions
- [ ] Frontend UI with HTML & CSS
- [ ] Interactive visualizations for recommendations
- [ ] REST API endpoint for model predictions
- [ ] Deployment (Render, Hugging Face Spaces, or similar)

---

### 🚀 Getting Started (coming soon)

Once the app is integrated, users will be able to:
- Enter soil parameters via a web form
- Receive predicted NPK values and yield estimation
- View visual feedback and suggestions

---

### 🤝 Contributing

Want to help? You're welcome! Please open an issue or PR if you’d like to collaborate on:
- Flask integration
- UI design
- Model improvements
- Dataset contributions

---

### 📄 License

This project will be released under the MIT License.

---

