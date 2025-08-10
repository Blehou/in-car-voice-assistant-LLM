import json
import pandas as pd
import random
import os
import joblib  # for saving the model
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay


from pathlib import Path

# === Paths to dataset files ===
HOBBY_PATH = Path("intent_classifier/Dataset/hobby.json")
RESTAURANT_PATH = Path("intent_classifier/Dataset/Restaurant.json")
STATION_PATH = Path("intent_classifier/Dataset/Station.json")


# === Load all three intent-specific datasets ===
with open(HOBBY_PATH, "r") as f1:
    hobby_data = json.load(f1)

with open(RESTAURANT_PATH, "r") as f2:
    restaurant_data = json.load(f2)

with open(STATION_PATH, "r") as f3:
    station_data = json.load(f3)

# === Combine and shuffle all data ===
all_data = hobby_data + restaurant_data + station_data
random.shuffle(all_data)  # ensure the dataset is well mixed

# === Plot the distribution of intents ===
plt.figure(figsize=(10, 6))
intent_counts = pd.Series([item['intent'] for item in all_data]).value_counts()
intent_counts.plot(kind='bar', title='Intent Distribution')
plt.xlabel('Intent')
plt.ylabel('Count')
plt.xticks(rotation=45)  # ou 30, 60, etc.
plt.tight_layout() # adjust layout to prevent clipping of tick-labels

# === Save to file
plt.savefig("C:/Jean Eudes Folder/Jean_Eudes/EMSE&Cranfield/Cranfield/Individual Research Project - Thesis/Thesis/Code/AI_IRP_LLM/intent_classifier/Visualisation/intent_distribution.png")
print("Graph saved as 'intent_distribution.png'")

# === Show the plot
plt.show()

# === Convert into a pandas DataFrame ===
df = pd.DataFrame(all_data)
## print(df.head(10))

# === Separate features (text) and labels (intent) ===
X = df["text"]
y = df["intent"]

# === Split the data into training and testing sets (80% / 20%)
# stratify=y ensures class balance is preserved in both sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# === Define a simple classification pipeline:
# 1. Convert text to TF-IDF features (with unigrams and bigrams)
# 2. Train a Logistic Regression model
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
    ('clf', LogisticRegression(max_iter=1000))
])

# === Train the model on the training set
pipeline.fit(X_train, y_train)

# === Evaluate the model on the test set
y_pred = pipeline.predict(X_test)
print("Classification Report:")
print(classification_report(y_test, y_pred))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# === Visualize the confusion matrix
cm = confusion_matrix(y_test, y_pred, labels=pipeline.classes_)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=pipeline.classes_)
disp.title = "Confusion Matrix"
disp.plot()

# Save to file
plt.savefig("C:/Jean Eudes Folder/Jean_Eudes/EMSE&Cranfield/Cranfield/Individual Research Project - Thesis/Thesis/Code/AI_IRP_LLM/intent_classifier/Visualisation/confusion_matrix.png")
print("Graph saved as 'confusion_matrix.png'")

# Show the confusion matrix plot
plt.show()

# === Save the trained model to disk for future use
output_model_path = "intent_classifier.pkl"
joblib.dump(pipeline, output_model_path)

print(f"\n Model saved as '{output_model_path}'")
