"""
train.py
--------
This script trains a Multinomial Naive Bayes spam classifier.

HOW IT WORKS (simple terms):
1. We load the spam.csv dataset (messages labeled "spam" or "ham")
2. We convert text messages into numbers using CountVectorizer
   (counts how many times each word appears — like a word frequency counter)
3. We train a Naive Bayes model (a fast, effective text classifier)
4. We save both the model and the vectorizer as .pkl files
   so the Flask app can use them without re-training every time.

Run this ONCE before starting the Flask app:
    python train.py
"""

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

# ─────────────────────────────────────────────
# Step 1: Load the dataset
# ─────────────────────────────────────────────
print("[*] Loading dataset...")

dataset_path = os.path.join("dataset", "spam.csv")

# Read CSV — it has two columns: 'label' (spam/ham) and 'message'
df = pd.read_csv(dataset_path)

print(f"    Loaded {len(df)} messages")
print(f"    Spam count : {len(df[df['label'] == 'spam'])}")
print(f"    Ham count  : {len(df[df['label'] == 'ham'])}")

# ─────────────────────────────────────────────
# Step 2: Prepare features (X) and labels (y)
# ─────────────────────────────────────────────
X = df["message"]   # The actual text messages
y = df["label"]     # The labels: "spam" or "ham"

# ─────────────────────────────────────────────
# Step 3: Split into training and testing sets
# ─────────────────────────────────────────────
# 80% for training, 20% for testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ─────────────────────────────────────────────
# Step 4: Convert text to numbers using CountVectorizer
# ─────────────────────────────────────────────
# CountVectorizer builds a vocabulary from all words
# and represents each message as a word-count vector.
print("\n[*] Vectorizing text (converting words to numbers)...")

vectorizer = CountVectorizer(
    lowercase=True,       # convert everything to lowercase
    stop_words="english", # remove common words like "the", "is", "at"
)

X_train_vec = vectorizer.fit_transform(X_train)  # learn vocab + transform train set
X_test_vec  = vectorizer.transform(X_test)        # only transform test set (no learning)

print(f"    Vocabulary size: {len(vectorizer.vocabulary_)} unique words")

# ─────────────────────────────────────────────
# Step 5: Train the Naive Bayes model
# ─────────────────────────────────────────────
# MultinomialNB works great for word-count features.
# It calculates the probability of a message being spam vs ham.
print("\n[*] Training Multinomial Naive Bayes model...")

model = MultinomialNB()
model.fit(X_train_vec, y_train)

print("    Model trained successfully!")

# ─────────────────────────────────────────────
# Step 6: Evaluate the model
# ─────────────────────────────────────────────
print("\n[*] Evaluating model on test set...")

y_pred = model.predict(X_test_vec)
accuracy = accuracy_score(y_test, y_pred)

print(f"    Accuracy: {accuracy * 100:.2f}%")
print("\n   Detailed Report:")
print(classification_report(y_test, y_pred))

# ─────────────────────────────────────────────
# Step 7: Save the model and vectorizer
# ─────────────────────────────────────────────
# We use pickle to save Python objects to disk.
# This way Flask can load them instantly without re-training.
print("[*] Saving model and vectorizer...")

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("    model.pkl saved")
print("    vectorizer.pkl saved")
print("\n[DONE] Training complete! You can now run: python app.py")
