"""
app.py
------
Flask backend for the Explainable Spam & Phishing Detector.

HOW IT WORKS (simple terms):
1. The app loads the pre-trained ML model and vectorizer on startup.
2. When a user submits a message via the web UI:
   - The message is vectorized (converted to numbers)
   - The model predicts: spam or ham
   - The confidence score (%) is calculated
   - An explainability engine checks for suspicious keywords & patterns
3. All results are sent back as JSON to the frontend.

Routes:
   GET  /          → serves the main HTML page
   POST /predict   → accepts JSON message, returns prediction + explanation
"""

import re
import pickle
import os
from flask import Flask, request, jsonify, render_template

# ─────────────────────────────────────────────
# Initialize Flask app
# ─────────────────────────────────────────────
app = Flask(__name__)

# ─────────────────────────────────────────────
# Load the trained model and vectorizer
# ─────────────────────────────────────────────
MODEL_PATH      = "model.pkl"
VECTORIZER_PATH = "vectorizer.pkl"

if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
    raise FileNotFoundError(
        "❌ model.pkl or vectorizer.pkl not found!\n"
        "   Please run: python train.py   first."
    )

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(VECTORIZER_PATH, "rb") as f:
    vectorizer = pickle.load(f)

print("[OK] Model and vectorizer loaded successfully.")

# ─────────────────────────────────────────────
# Explainability Engine
# ─────────────────────────────────────────────

# Common spam/phishing keywords (used for highlighting + explanations)
SPAM_KEYWORDS = [
    "free", "win", "winner", "click", "offer", "urgent", "lottery",
    "now", "prize", "cash", "reward", "claim", "selected", "congratulations",
    "exclusive", "limited", "guaranteed", "act", "earn", "money",
    "bonus", "upgrade", "membership", "discount", "cheap", "buy",
    "call", "text", "subscribe", "unsubscribe", "credit", "loan"
]

URGENCY_WORDS = [
    "urgent", "immediately", "now", "today", "expires", "limited", "hurry",
    "act", "fast", "quick", "instant", "deadline", "last chance", "expiring"
]

# URL pattern to detect phishing links
URL_PATTERN = re.compile(
    r"(https?://[^\s]+|www\.[^\s]+|\b\w+\.(com|net|org|xyz|info|biz|ru|tk|click)[^\s]*)",
    re.IGNORECASE
)

# Symbols that appear frequently in spam (currency, exclamation, etc.)
EXCESSIVE_SYMBOL_PATTERN = re.compile(r"[!£$€@#%&*]{2,}")

# ─────────────────────────────────────────────
# Scammer Intent Detection Patterns
# ─────────────────────────────────────────────

# Patterns to detect what the scammer wants to achieve
MONEY_THEFT_KEYWORDS = [
    "win", "winner", "prize", "cash", "money", "reward", "claim", "payment",
    "transfer", "deposit", "account", "loan", "credit", "debt", "fee",
    "pay", "bitcoin", "cryptocurrency", "investment", "profit", "earn"
]

DATA_THEFT_KEYWORDS = [
    "verify", "confirm", "update", "security", "password", "account",
    "login", "credentials", "personal", "information", "details", "ssn",
    "social security", "card number", "cvv", "pin", "identity", "verification"
]

PANIC_KEYWORDS = [
    "urgent", "immediately", "suspend", "suspended", "blocked", "locked",
    "compromised", "unauthorized", "fraud", "fraudulent", "alert", "warning",
    "expires", "expired", "deadline", "last chance", "act now", "emergency"
]

MALWARE_KEYWORDS = [
    "click", "download", "install", "update", "software", "antivirus",
    "security update", "patch", "link", "attachment", "file"
]


def explain_message(message: str):
    """
    Analyze a message and return:
      - suspicious_words : list of flagged words found in the message
      - explanations     : list of human-readable reason strings

    HOW IT WORKS:
    We simply check the message text against known spam patterns.
    This is a RULE-BASED system — no ML needed here, pure logic.
    """
    msg_lower = message.lower()
    words_in_msg = re.findall(r"\b\w+\b", msg_lower)

    suspicious_words = []
    explanations = []

    # --- Check 1: Spam keywords ---
    for keyword in SPAM_KEYWORDS:
        if keyword in words_in_msg:
            if keyword not in suspicious_words:
                suspicious_words.append(keyword)
                explanations.append(f"⚠️ Contains suspicious keyword: <b>{keyword}</b>")

    # --- Check 2: Urgency words ---
    for word in URGENCY_WORDS:
        if word in msg_lower and word not in suspicious_words:
            suspicious_words.append(word)
            explanations.append(f"🚨 Contains urgency word: <b>{word}</b>")

    # --- Check 3: URLs (phishing indicator) ---
    urls_found = URL_PATTERN.findall(message)
    if urls_found:
        explanations.append("🔗 Contains a URL — possible phishing link detected")
        # Add 'url' as a suspicious marker for frontend highlighting
        suspicious_words.append("http")
        suspicious_words.append("www")

    # --- Check 4: Excessive symbols ---
    if EXCESSIVE_SYMBOL_PATTERN.search(message):
        explanations.append("💲 Contains excessive symbols ($$, !!, ££) — common in spam")

    # --- Check 5: ALL CAPS check ---
    words_only = re.sub(r"[^a-zA-Z ]", "", message)
    if words_only and sum(1 for c in words_only if c.isupper()) / max(len(words_only), 1) > 0.5:
        explanations.append("🔠 Message uses excessive CAPS — typical spam behavior")

    # Remove duplicates while preserving order
    suspicious_words = list(dict.fromkeys(suspicious_words))

    return suspicious_words, explanations


def detect_scammer_intent(message: str, prediction: str):
    """
    Reverse Intent Detection: Analyze what the scammer is trying to achieve.
    
    Returns a list of detected intents with icons and descriptions.
    Only runs if prediction is "spam".
    """
    if prediction != "spam":
        return []
    
    msg_lower = message.lower()
    intents = []
    
    # Check for money theft intent
    money_matches = sum(1 for word in MONEY_THEFT_KEYWORDS if word in msg_lower)
    if money_matches >= 2:
        intents.append({
            "icon": "💰",
            "goal": "Steal Money",
            "description": "Scammer wants you to send money or provide payment information"
        })
    
    # Check for data theft intent
    data_matches = sum(1 for word in DATA_THEFT_KEYWORDS if word in msg_lower)
    if data_matches >= 2:
        intents.append({
            "icon": "🔐",
            "goal": "Steal Personal Data",
            "description": "Scammer is trying to harvest your login credentials or personal information"
        })
    
    # Check for panic creation intent
    panic_matches = sum(1 for word in PANIC_KEYWORDS if word in msg_lower)
    if panic_matches >= 2:
        intents.append({
            "icon": "😱",
            "goal": "Create Panic",
            "description": "Scammer uses urgency and fear to make you act without thinking"
        })
    
    # Check for malware installation intent
    malware_matches = sum(1 for word in MALWARE_KEYWORDS if word in msg_lower)
    urls_present = bool(URL_PATTERN.search(message))
    if malware_matches >= 2 and urls_present:
        intents.append({
            "icon": "🦠",
            "goal": "Install Malware",
            "description": "Scammer wants you to click a link or download malicious software"
        })
    
    # If spam but no specific intent detected, add a generic one
    if not intents:
        intents.append({
            "icon": "🎯",
            "goal": "Deceptive Intent",
            "description": "Scammer is attempting to deceive or manipulate you"
        })
    
    return intents


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    """
    Accept a JSON payload with a 'message' field.
    Returns a JSON response with:
      - prediction      : "spam" or "ham"
      - confidence      : percentage (0–100)
      - suspicious_words: list of flagged words
      - explanation     : list of reason strings
    """
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    message = data["message"].strip()

    if not message:
        return jsonify({"error": "Message is empty"}), 400

    # --- ML Prediction ---
    # 1. Convert message to a word-count vector (same process as training)
    message_vec = vectorizer.transform([message])

    # 2. Predict class label ("spam" or "ham")
    prediction = model.predict(message_vec)[0]

    # 3. Get probability scores for both classes
    probabilities = model.predict_proba(message_vec)[0]

    # 4. Map class labels to probabilities
    classes = model.classes_.tolist()     # e.g., ["ham", "spam"]
    prob_dict = dict(zip(classes, probabilities))

    # Confidence = probability of the predicted class, as a percentage
    confidence = round(prob_dict[prediction] * 100, 2)

    # --- Explainability ---
    suspicious_words, explanations = explain_message(message)

    # --- Scammer Intent Detection ---
    scammer_intent = detect_scammer_intent(message, prediction)

    # If ham but suspicious words found, add a note
    if prediction == "ham" and suspicious_words:
        explanations.insert(0, "ℹ️ Model predicts HAM, but some suspicious patterns were found:")

    # If spam with no pattern match, add a generic note
    if prediction == "spam" and not explanations:
        explanations.append("🤖 ML model detected spam patterns based on learned features.")
    # Build and return the JSON response
    response = {
        "prediction":       prediction,        # "spam" or "ham"
        "confidence":       confidence,         # e.g. 97.43
        "suspicious_words": suspicious_words,   # ["free", "win", ...]
        "explanation":      explanations,       # ["Contains keyword: free", ...]
        "scammer_intent":   scammer_intent      # [{"icon": "💰", "goal": "Steal Money", ...}]
    }

    return jsonify(response)


# ─────────────────────────────────────────────
# Run the Flask development server
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("[START] Starting Spam Detector server at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
