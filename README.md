# AI Health Assistant

A **production-ready AI-powered Health Assistant** for analyzing patient symptoms, summarizing medical reports, predicting disease risk, and providing personalized preventive recommendations. Built with **FastAPI**, **PyTorch**, and **modern NLP models**.

---

## **Features**

- **Symptom Analysis**: Analyze patient-reported symptoms and return top probable conditions.  
- **Medical Report Summarization**: Generate concise summaries of medical reports using NLP.  
- **Disease Risk Prediction**: Predict patient-specific disease risks with probability scores.  
- **Personalization Engine**: Apply patient-specific weights and maintain history for improved recommendations.  
- **Preventive Care Recommendations**: Suggest actionable steps based on disease predictions.  
- **Batch Predictions**: Support for multiple patients at once.  
- **Logging & History**: Tracks patient interactions and model outputs for auditing.

---

## **Folder Structure**

ai_module/
│
├── app/
│ ├── init.py
│ ├── main.py
│ ├── routes/
│ │ ├── analyze.py
│ │ ├── summarize.py
│ │ ├── predict.py
│ │ └── personalization.py
│ ├── services/
│ │ ├── symptom_model.py
│ │ ├── summary_model.py
│ │ ├── disease_model.py
│ │ ├── recommender.py
│ │ └── personalization_engine.py
│ ├── utils/
│ │ ├── preprocess.py
│ │ ├── postprocess.py
│ │ └── logger.py
│ └── config.py
├── models/
│ ├── pretrained/
│ └── personalized/
├── data/
├── notebooks/
├── tests/
├── requirements.txt
├── Dockerfile
└── README.md

---

## **Installation**

### 1. Clone the repository
```bash
git clone <repo_url>
cd ai_module
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install --upgrade pip
pip install -r requirements.txt

## Running with Docker