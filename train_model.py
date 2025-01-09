import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import classification_report
import pandas as pd

# Load dataset
def load_data(file_path="data.csv"):
    """Loads the dataset and returns text and labels."""
    data = pd.read_csv(file_path)  # Ensure this CSV contains 'text' and 'sentiment' columns
    return data['text'], data['sentiment']

# Train model
def train_model():
    """Trains and saves the sentiment analysis model."""
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Preprocessing and vectorization
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Train the model
    model = SVC(kernel='linear')
    model.fit(X_train_vec, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test_vec)
    print(classification_report(y_test, y_pred))

    # Save the model and vectorizer
    with open("sentiment_model.pkl", "wb") as model_file:
        pickle.dump(model, model_file)

    with open("vectorizer.pkl", "wb") as vec_file:
        pickle.dump(vectorizer, vec_file)

if __name__ == "__main__":
    train_model()
