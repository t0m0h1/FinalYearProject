from flask import Flask, render_template, request, jsonify
import pickle
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Initialise Flask app
app = Flask(__name__)

# Load model and vectorizer
with open("sentiment_model.pkl", "rb") as model_file:
    sentiment_model = pickle.load(model_file)

with open("vectorizer.pkl", "rb") as vec_file:
    vectorizer = pickle.load(vec_file)

# Preprocess text
def preprocess_text(text):
    """Cleans and preprocesses input text."""
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text.lower())
    filtered_words = [word for word in word_tokens if word.isalnum() and word not in stop_words]
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_words]
    return " ".join(lemmatized_words)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form['feelings']
    preprocessed_input = preprocess_text(user_input)
    vectorized_input = vectorizer.transform([preprocessed_input])
    sentiment = sentiment_model.predict(vectorized_input)[0]

    # Generate suggestion
    suggestion = "Positive!" if sentiment == 1 else "Negative!"
    return jsonify({'suggestion': suggestion})

if __name__ == "__main__":
    app.run(debug=True)
