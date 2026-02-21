# 🛡️ SpamShield AI — Explainable Spam & Phishing Detector

> An ML-powered web app that detects spam and phishing messages with explainability — built with Flask, Scikit-learn, and vanilla JS.

---

## 📁 Project Structure

```
demo/
│
├── app.py             ← Flask backend server
├── train.py           ← ML model training script
├── model.pkl          ← Saved Naive Bayes model (auto-generated)
├── vectorizer.pkl     ← Saved CountVectorizer (auto-generated)
│
├── templates/
│   └── index.html     ← Main web page (served by Flask)
│
├── static/
│   ├── style.css      ← Dark glassmorphism UI styles
│   └── script.js      ← Frontend logic & API calls
│
├── dataset/
│   └── spam.csv       ← Labeled spam/ham training data
│
└── README.md          ← You are here!
```

---

## ⚡ Quick Start (3 Steps)

### Step 1 — Install Dependencies

```bash
pip install flask scikit-learn pandas
```

### Step 2 — Train the Model

```bash
python train.py
```

This reads `dataset/spam.csv`, trains a Naive Bayes classifier, and saves:
- `model.pkl` — the trained ML model
- `vectorizer.pkl` — the text vectorizer

### Step 3 — Run the App

```bash
python app.py
```

Then open your browser and visit: **http://127.0.0.1:5000**

---

## 🧠 How It Works (Simple Explanation)

### 1. Machine Learning (train.py)
- Loads messages labeled as **spam** or **ham** (not spam)
- Uses **CountVectorizer** to convert text → word-frequency numbers
- Trains a **Multinomial Naive Bayes** model — ideal for text classification
- Naive Bayes works by learning: *"If a message contains 'free', 'win', 'prize', how likely is it spam?"*

### 2. Flask Backend (app.py)
- `GET /` — serves the HTML page
- `POST /predict` — receives a message, vectorizes it, runs the ML model, then:
  - Returns `prediction` (spam/ham)
  - Returns `confidence` (how sure the model is, in %)
  - Returns `suspicious_words` (flagged keywords found)
  - Returns `explanation` (human-readable reasons)

### 3. Explainability Engine (inside app.py)
Rule-based system that checks:
- **Spam keywords**: free, win, click, offer, urgent, lottery, prize, etc.
- **Urgency words**: now, today, expires, immediately, hurry, etc.
- **URLs**: phishing links (http://, www.)
- **Excessive symbols**: !!, ££, $$
- **ALL CAPS**: typical spam behavior

### 4. Frontend (HTML + CSS + JS)
- User types a message → clicks Analyze
- JavaScript calls `/predict` via `fetch()` (no page reload)
- Suspicious words are highlighted in **red** in the message preview
- A confidence progress bar animates to the score
- Explanation list shows exactly why it was flagged

---

## 🔌 API Reference

### `POST /predict`

**Request:**
```json
{
  "message": "Congratulations! You've won a FREE iPhone. Click now!"
}
```

**Response:**
```json
{
  "prediction": "spam",
  "confidence": 97.43,
  "suspicious_words": ["free", "click", "win", "now"],
  "explanation": [
    "⚠️ Contains suspicious keyword: <b>free</b>",
    "⚠️ Contains suspicious keyword: <b>click</b>",
    "🚨 Contains urgency word: <b>now</b>"
  ]
}
```

---

## 🖼️ Screenshots

> _[Add screenshots here after running the app]_

| Homepage | Spam Detected | Safe Message |
|----------|---------------|--------------|
| ![home]() | ![spam]() | ![ham]() |

---

## 🧪 Test Messages

Try these in the app:

**Spam:**
```
WINNER!! You have been selected to receive a £900 prize. Call 09061701461 now to claim. Valid 12 hours only!
```

**Safe:**
```
Hey, are you free Saturday for the team lunch? Let me know what time works!
```

**Phishing:**
```
URGENT: Your account is at risk. Verify now at http://secure-banklogin.xyz to avoid suspension.
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3 (Glassmorphism), Vanilla JS |
| Backend | Python, Flask |
| ML Model | Scikit-learn, Multinomial Naive Bayes |
| Vectorizer | CountVectorizer |
| Explainability | Rule-based keyword engine |

---

## 📦 Requirements

```
flask
scikit-learn
pandas
```

Install all at once:
```bash
pip install flask scikit-learn pandas
```

---

## 📜 License

MIT — Free to use for learning, hackathons, and personal projects.
