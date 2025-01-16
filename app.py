from flask import Flask, render_template, request, jsonify
import datetime
import pickle
import numpy as np
from tensorflow.keras.models import load_model
import nltk
from nltk.stem import WordNetLemmatizer
import random

# Initialise Flask app
app = Flask(__name__)

# Load model and necessary data
model = load_model('chatbot_model.h5')
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
lemmatiser = WordNetLemmatizer()

# Example data for FAQ and resources
FAQ = [
    {"question": "What is mental health?", "answer": "Mental health includes our emotional, psychological, and social well-being. It affects how we think, feel, and act."},
    {"question": "How can I manage stress?", "answer": "You can manage stress by exercising, practising mindfulness, staying organised, and seeking support from friends or professionals."}
]

CRISIS_HELPLINES = [
    {"name": "National Suicide Prevention Lifeline", "number": "1-800-273-TALK"},
    {"name": "Crisis Text Line", "text": "Text HOME to 741741"}
]

GUIDED_EXERCISES = {
    "mindfulness": "Take a moment to sit comfortably and focus on your breath. Inhale deeply through your nose for 4 seconds, hold for 4 seconds, and exhale through your mouth for 4 seconds. Repeat for 5 minutes.",
    "breathing": "Try the 4-7-8 technique: Breathe in through your nose for 4 seconds, hold your breath for 7 seconds, and exhale slowly through your mouth for 8 seconds. Repeat 4 times."
}

# Preprocess input
def preprocess_input(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatiser.lemmatize(word.lower()) for word in sentence_words]
    bag = [1 if word in sentence_words else 0 for word in words]
    return np.array(bag)

# Predict response tag
def predict_tag(sentence):
    bow = preprocess_input(sentence)
    res = model.predict(np.array([bow]))[0]
    threshold = 0.25  # Confidence threshold
    results = [[i, r] for i, r in enumerate(res) if r > threshold]
    results.sort(key=lambda x: x[1], reverse=True)
    return classes[results[0][0]] if results else None

# Map tag to response
def get_response(tag, intents_file='intents.json'):
    try:
        intents = pickle.load(open('intents.pkl', 'rb'))
        for intent in intents['intents']:
            if intent['tag'] == tag:
                return random.choice(intent['responses'])
        return "I'm sorry, I didn't quite understand that."
    except FileNotFoundError:
        return "Error: Intents file not found."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')  # HTML for the chatbot interface

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').lower()
    response = ""

    # Predict response dynamically
    tag = predict_tag(user_message)
    if tag:
        response = get_response(tag)
    else:
        response = "I'm here to help! You can ask about exercises, crisis support, or FAQs."

    return jsonify({"response": response})

@app.route('/time', methods=['GET'])
def get_time():
    return jsonify({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

if __name__ == '__main__':
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    app.run(debug=True)



















# original code for reference:

# from flask import Flask, render_template, request, jsonify
# import datetime

# app = Flask(__name__)

# # Example data for FAQ and resources
# FAQ = [
#     {"question": "What is mental health?", "answer": "Mental health includes our emotional, psychological, and social well-being. It affects how we think, feel, and act."},
#     {"question": "How can I manage stress?", "answer": "You can manage stress by exercising, practicing mindfulness, staying organized, and seeking support from friends or professionals."}
# ]

# CRISIS_HELPLINES = [
#     {"name": "National Suicide Prevention Lifeline", "number": "1-800-273-TALK"},
#     {"name": "Crisis Text Line", "text": "Text HOME to 741741"}
# ]

# GUIDED_EXERCISES = {
#     "mindfulness": "Take a moment to sit comfortably and focus on your breath. Inhale deeply through your nose for 4 seconds, hold for 4 seconds, and exhale through your mouth for 4 seconds. Repeat for 5 minutes.",
#     "breathing": "Try the 4-7-8 technique: Breathe in through your nose for 4 seconds, hold your breath for 7 seconds, and exhale slowly through your mouth for 8 seconds. Repeat 4 times."
# }

# @app.route('/')
# def home():
#     return render_template('index.html')  # Placeholder HTML for the chatbot interface

# @app.route('/chat', methods=['POST'])
# def chat():
#     user_message = request.json.get('message', '').lower()
#     response = ""

#     if "help" in user_message or "crisis" in user_message:
#         response = "Here are some crisis helplines:\n" + "\n".join([f"{line['name']}: {line.get('number', line.get('text'))}" for line in CRISIS_HELPLINES])
#     elif "exercise" in user_message or "mindfulness" in user_message:
#         response = GUIDED_EXERCISES.get("mindfulness", "Let's take a mindful moment.")
#     elif "breathing" in user_message:
#         response = GUIDED_EXERCISES.get("breathing", "Let's focus on our breathing.")
#     elif "faq" in user_message:
#         response = "Here are some frequently asked questions:\n" + "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in FAQ])
#     else:
#         response = "I'm here to help! You can ask about exercises, crisis support, or FAQs."

#     return jsonify({"response": response})

# @app.route('/time', methods=['GET'])
# def get_time():
#     return jsonify({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

# if __name__ == '__main__':
#     app.run(debug=True)
