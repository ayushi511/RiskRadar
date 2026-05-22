# 🌍 RiskRadar — AI-Powered Disaster Monitoring Platform

RiskRadar is a full-stack disaster monitoring and prediction platform that combines real-time disaster alerts with machine learning-based geospatial risk analysis.

## 🚀 Features

* 🗺️ Live global disaster monitoring with interactive maps
* 🌋 Real-time disaster alerts including earthquakes, floods, cyclones, wildfires, and volcanoes
* 🤖 AI-powered risk prediction using historical disaster data
* 🔥 Heatmap visualization for disaster density analysis
* 📡 Auto-refresh system updating alerts every 5 minutes
* 🔍 Disaster filtering and searchable live alerts
* 📊 Analytics dashboard with:

  * Disaster distribution charts
  * Weekly trend analysis
  * Severity breakdown
  * Critical alert monitoring
  * Most affected regions
* ✨ Modern UI with glassmorphism cards and responsive design

---

## 🛠️ Tech Stack

### Backend

* Python
* FastAPI
* APScheduler
* scikit-learn
* GDACS API
* USGS API

### Frontend

* HTML
* CSS
* JavaScript
* Leaflet.js

### Deployment

* Frontend: Vercel
* Backend: Render

---

## 📊 Machine Learning

* Trained on 6 years of historical GDACS disaster data
* Achieved 85% test accuracy and 77% cross-validation accuracy
* Predicts Low / High / Critical risk levels for global regions

---

## ⚙️ Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn apscheduler requests pandas scikit-learn joblib numpy
python -m uvicorn main:app --reload
```

### Train ML Model

```bash
GET http://localhost:8000/api/ml/train
```

### Frontend

Open:

```bash
frontend/public/map.html
```

in your browser.

---

## 🌐 Live Demo

Frontend: https://risk-radar-xrj3.vercel.app/

---

## 👩‍💻 Author

Ayushi Srivastava
