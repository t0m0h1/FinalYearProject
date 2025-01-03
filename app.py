from flask import Flask, render_template, request, jsonify
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from transformers import pipeline

# Initialize Flask app
app = Flask(__name__)

# Sentiment Analysis Pipeline using Huggingface
sentiment_analyzer = pipeline("sentiment-analysis")

# NLTK Resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Preprocess Text
def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text.lower())
    filtered_words = [word for word in word_tokens if word not in stop_words]
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_words]
    return " ".join(lemmatized_words)

# Train Sentiment Model (simplified example)
def train_sentiment_model():
    pass

# Initialize the sentiment model
vectorizer, sentiment_model = train_sentiment_model()

# Function to predict sentiment using ML model
def predict_sentiment(text):
    processed_text = preprocess_text(text)
    vectorized_text = vectorizer.transform([processed_text])
    sentiment = sentiment_model.predict(vectorized_text)
    return sentiment[0]

# Function to provide suggestions based on sentiment
def get_suggestions(sentiment):
    if sentiment == 0:
        return "You might be feeling down. It's okay to reach out to someone, take a break, or try some stress-relief activities."
    elif sentiment == 1:
        return "Great to hear that you're feeling positive! Keep it up and stay connected with your support network."
    else:
        return "It seems like you're uncertain. Maybe talking to someone or reflecting might help clarify things."


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    student_input = request.form['feelings']
    
    # Sentiment analysis using Huggingface model
    sentiment = sentiment_analyzer(student_input)[0]['label']
    if sentiment == 'NEGATIVE':
        sentiment = 0  # Negative sentiment
    else:
        sentiment = 1  # Positive sentiment

    # Get suggestion based on sentiment
    suggestion = get_suggestions(sentiment)

    return jsonify({'suggestion': suggestion})

if __name__ == '__main__':
    app.run(debug=True)
