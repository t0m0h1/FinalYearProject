# new code
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

# Load the trained model and vectorizer once
model = None
vectorizer = None

def load_model():
    global model, vectorizer
    if model is None or vectorizer is None:
        with open("sentiment_model.pkl", "rb") as model_file:
            model = pickle.load(model_file)
        with open("vectorizer.pkl", "rb") as vec_file:
            vectorizer = pickle.load(vec_file)
    return model, vectorizer

def predict_sentiment(text):
    model, vectorizer = load_model()
    vectorized_input = vectorizer.transform([text])
    sentiment = model.predict(vectorized_input)[0]
    return sentiment
