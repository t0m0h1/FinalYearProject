from flask import Flask, render_template, request, jsonify
import datetime
import pickle
import numpy as np
from tensorflow.keras.models import load_model
import nltk
from nltk.stem import WordNetLemmatizer
import random
import json
import sqlite3


# Initialise Flask app
app = Flask(__name__)


lemmatiser = WordNetLemmatizer()

try:
    model = load_model('chatbot_model.h5')
    words = pickle.load(open('words.pkl', 'rb'))
    classes = pickle.load(open('classes.pkl', 'rb'))
except (OSError, FileNotFoundError) as e:
    print(f"Error loading model/data: {e}")
    model, words, classes = None, [], []



# data for FAQ and resources
FAQ = {
    "General Mental Health": [
        {
            "questions": ["What is mental health?", "Can you define mental health?"],
            "answer": "Mental health includes our emotional, psychological, and social well-being."
        }
    ],
    "Stress Management": [
        {
            "questions": ["How do I manage stress?", "What are some stress relief techniques?"],
            "answer": "You can manage stress by exercising, practicing mindfulness, and seeking support."
        },
        {
            "questions": ["What are some quick ways to relieve stress?"],
            "answer": "Try deep breathing, progressive muscle relaxation, or listening to calming music."
        }
    ]
}


CRISIS_HELPLINES = {
    "USA": [
        {
            "name": "National Suicide Prevention Lifeline",
            "phone": "1-800-273-TALK",
            "text": "Text HOME to 741741",
            "chat": "https://suicidepreventionlifeline.org/chat",
            "available": "24/7"
        }
    ],
    "UK": [
        {
            "name": "Samaritans",
            "phone": "116 123",
            "email": "jo@samaritans.org",
            "chat": "https://www.samaritans.org",
            "available": "24/7"
        }
    ]
}


GUIDED_EXERCISES = {
    "breathing": [
        {
            "name": "4-7-8 Breathing",
            "difficulty": "Beginner",
            "duration": "5 minutes",
            "instructions": "Breathe in for 4 seconds, hold for 7 seconds, and exhale for 8 seconds.",
        },
        {
            "name": "Box Breathing",
            "difficulty": "Intermediate",
            "duration": "5 minutes",
            "instructions": "Inhale for 4 seconds, hold for 4 seconds, exhale for 4 seconds, hold for 4 seconds. Repeat.",
        }
    ],
    "mindfulness": [
        {
            "name": "5-4-3-2-1 Grounding",
            "difficulty": "Beginner",
            "duration": "5 minutes",
            "instructions": "Identify 5 things you see, 4 things you feel, 3 things you hear, 2 things you smell, and 1 thing you taste.",
        },
        {
            "name": "Body Scan Meditation",
            "difficulty": "Advanced",
            "duration": "10 minutes",
            "instructions": "Slowly bring attention to each part of your body, from your toes to your head, noticing any sensations.",
        }
    ]
}


# add more to this data as this is currently placeholder data.



# Preprocess input
# This function has been updated to check the array length matches model if the model has been retrained/ modified
def preprocess_input(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatiser.lemmatize(word.lower()) for word in sentence_words]

    # Ensure consistent size
    bag = np.zeros(len(words))
    for word in sentence_words:
        if word in words:
            bag[words.index(word)] = 1

    return np.array(bag)




# Predict response tag
def predict_tag(sentence):
    bow = preprocess_input(sentence)
    res = model.predict(np.array([bow]))[0]
    threshold = 0.25  # Confidence threshold at 25%
    results = [[i, r] for i, r in enumerate(res) if r > threshold]
    results.sort(key=lambda x: x[1], reverse=True)
    return classes[results[0][0]] if results else None


# Map tag to response    
def get_response(tag, intents_file='intents.json'):
    try:
        with open(intents_file, 'r') as file:
            intents = json.load(file)
        for intent in intents['intents']:
            if intent['tag'] == tag:
                return random.choice(intent['responses'])
        return "I'm sorry, I didn't quite understand that."
    except FileNotFoundError:
        return "Error: Intents file not found."
    except Exception as e:
        return f"Error: {str(e)}"





# Routes - these are the functions the app will respond to
@app.route('/')
def home():
    return render_template('index.html')  # HTML for the chatbot interface



# app will find related faqs if no confident prediction is made.
def find_related_faqs(user_message):
    user_message = user_message.lower()
    for faq in FAQ:
        if any(word in user_message for word in faq["question"].lower().split()):
            return faq["answer"]
    return None

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').lower()
    
    if not isinstance(user_message, str):
        return jsonify({"response": "Invalid input."})
    
    tag = predict_tag(user_message)
    if tag:
        response = get_response(tag)
    else:
        response = find_related_faqs(user_message) or "I'm here to help! You can ask about exercises, crisis support, or FAQs."

    return jsonify({"response": response})








@app.route('/time', methods=['GET'])
def get_time():
    return jsonify({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})




# flask route to save data
@app.route('/save_mood', methods=['POST'])
def save_mood():
    data = request.json
    mood = data['mood']
    date = data['date']

    # Save to SQLite database
    conn = sqlite3.connect('moods.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO moods (date, mood) VALUES (?, ?)", (date, mood))
    conn.commit()
    conn.close()

    return jsonify({"message": "Mood saved successfully"})



# flask route to get data
@app.route('/get_moods', methods=['GET'])
def get_moods():
    conn = sqlite3.connect('moods.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, mood FROM moods")
    moods = cursor.fetchall()
    conn.close()

    return jsonify(moods)



# Create SQLite database if it doesn't exist
def init_db():
    conn = sqlite3.connect('moods.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS moods (id INTEGER PRIMARY KEY, date TEXT, mood TEXT)''')
    conn.commit()
    conn.close()






# driver code
if __name__ == '__main__':
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    
    init_db()  # Run this before starting the app
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
