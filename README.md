# 🌍 RiskRadar — AI-Powered Disaster Monitoring System

A full-stack disaster prediction and monitoring platform that combines real-time disaster alerts with machine learning to predict high-risk zones globally.

## 🚀 Features

- 🗺️ **Live Global Map** — Real-time disaster markers (earthquakes, floods, wildfires, cyclones, volcanoes)
- 🧠 **AI Risk Zones** — ML model predicts historically high-risk regions based on 6 years of data
- 🔥 **Heatmap Mode** — Density visualization of disaster activity
- 📡 **Auto-refresh** — Live alerts updated every 5 minutes
- 🔍 **Filter & Search** — Filter by disaster type and severity

## 🛠️ Tech Stack

**Backend:** Python, FastAPI, APScheduler, scikit-learn, GDACS API, USGS API

**Frontend:** HTML, CSS, JavaScript, Leaflet.js

## 📊 ML Model

- Trained on 6 years of real GDACS historical data
- 85% test accuracy, 77% cross-validation accuracy
- Predicts Low / High / Critical risk per global region

## ⚙️ Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn apscheduler requests pandas scikit-learn joblib numpy
python -m uvicorn main:app --reload
```

Train the model: GET http://localhost:8000/api/ml/train

Open frontend/public/map.html in browser
