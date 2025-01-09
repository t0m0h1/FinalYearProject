# Using code we have modularised in other folders in repository

from flask import Flask, render_template, request, jsonify
from models.sentiment_model import predict_sentiment
from utils.preprocess import preprocess_text

# Initialise Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form['feelings']
    preprocessed_input = preprocess_text(user_input)
    sentiment = predict_sentiment(preprocessed_input)
    
    suggestion = "Positive!" if sentiment == 1 else "Negative!"
    return jsonify({'suggestion': suggestion})

if __name__ == "__main__":
    app.run(debug=True)
