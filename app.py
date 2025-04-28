# Flask imports 
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


from flask_cors import CORS # For cross-origin requests



# Other imports
import datetime
import pickle
import numpy as np
from tensorflow.keras.models import load_model
import nltk
from nltk.stem import WordNetLemmatizer
import random
import json
import sqlite3
from flask import jsonify




# Initialise Flask app
app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = '01' # I will change this later
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moods.db' # SQLite database for storing mood data - will be created in the same directory as the app
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Handle login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)



# ----- Database models ----

# Create user model (class user)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)


# Create gratitude log model
class GratitudeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    entry1 = db.Column(db.String(300))
    entry2 = db.Column(db.String(300))
    entry3 = db.Column(db.String(300))



# Define Mood model
class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100))
    mood = db.Column(db.String(50))


# Define JournalEntry model
class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)





# --- Flask-Login user loader function ---


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create database tables
with app.app_context():
    db.create_all()


# Route for signing up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered!', category='error')
            return redirect(url_for('signup'))

        # Hash password and add user to database
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method='sha256')
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created! You can now log in.', category='success')
        return redirect(url_for('login'))

    return render_template('signup.html')




# Route to render login form (GET request)
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')  # Assuming you have a 'login.html' template

# Route to handle login submission (POST request)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()  # Get the data sent from JavaScript
    email = data.get('email')
    password = data.get('password')

    # Check for missing fields
    if not email or not password:
        return jsonify({'message': 'Email and password are required!'}), 400

    # Attempt to authenticate user
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        login_user(user, remember=True)  # Log the user in using Flask-Login
        flash('Login successful!', category='success')
        return jsonify({'message': 'Login successful!', 'redirect': url_for('home')})

    flash('Invalid credentials, please try again.', category='error')
    return jsonify({'message': 'Invalid credentials, try again.'}), 401



# Route for gratitude logging
@app.route('/save_gratitude', methods=['POST'])
@login_required
def save_gratitude():
    data = request.json
    date = data['date']
    entry1 = data['entry1']
    entry2 = data['entry2']
    entry3 = data['entry3']

    existing = GratitudeLog.query.filter_by(user_id=current_user.id, date=date).first()
    if existing:
        return jsonify({"message": "You've already submitted gratitude for today."}), 400

    gratitude = GratitudeLog(
        user_id=current_user.id,
        date=date,
        entry1=entry1,
        entry2=entry2,
        entry3=entry3
    )
    db.session.add(gratitude)
    db.session.commit()

    return jsonify({"message": "Gratitude logged successfully!"})


# Route for viewing gratitude logs
@app.route('/gratitude_logs', methods=['GET'])
@login_required
def gratitude_logs():
    logs = GratitudeLog.query.filter_by(user_id=current_user.id).order_by(GratitudeLog.date.desc()).all()
    return jsonify([
        {
            "date": log.date,
            "entry1": log.entry1,
            "entry2": log.entry2,
            "entry3": log.entry3
        }
        for log in logs
    ])





# Route for logging out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='info')
    return redirect(url_for('login'))







# ---------------- Chatbot code ----------------

# Load model and data
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
    

 


# ---------------- Routes ----------------


# Routes - these are the functions the app will respond to
@app.route('/')
@login_required # This will redirect to the login page if the user is not logged in
def home():
    return render_template('index.html')  # HTML for the chatbot interface


@app.route('/save_journal', methods=['POST'])
@login_required
def save_journal():
    data = request.json
    date = data['date']
    content = data['content']

    existing_entry = JournalEntry.query.filter_by(user_id=current_user.id, date=date).first()
    if existing_entry:
        return jsonify({"message": "You've already written a journal for today."}), 400

    new_entry = JournalEntry(
        user_id=current_user.id,
        date=date,
        content=content
    )
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"message": "Journal entry saved successfully!"})


@app.route('/journal_logs', methods=['GET'])
@login_required
def journal_logs():
    logs = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.date.desc()).all()
    return jsonify([
        {
            "date": log.date,
            "content": log.content
        }
        for log in logs
    ])







# app will find related faqs if no confident prediction is made.
def find_related_faqs(user_message):
    user_message = user_message.lower()
    for faq in FAQ:
        if any(word in user_message for word in faq["question"].lower().split()):
            return faq["answer"]
    return None



# Function to be used for mood analysis 

# #####   Implement this later.
def analyze_input(user_input):
    lower_input = user_input.lower()

    if any(word in lower_input for word in ["stressed", "anxious", "overwhelmed", "worried"]):
        return "stress"
    elif any(word in lower_input for word in ["sad", "down", "upset", "depressed"]):
        return "sadness"
    elif any(word in lower_input for word in ["happy", "good", "great"]):
        return "positive"
    else:
        return "unknown"






# Chat routes with smart follow-up and coping strategies
import re

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').lower()

    if not isinstance(user_message, str):
        return jsonify({"response": "Invalid input."})

    # Start the conversation with a greeting if it's the first message
    if user_message == 'start':
        return jsonify({"response": f"Hello! How can I help you today?"})

    # Smart follow-up for negative mood expressions
    negative_keywords = [
        "okay", "bad", "sad", "down", "hopeless", "right", "overwhelmed", "good", "anxious", "scared", "depressed", "stressed"
    ]

    negative_patterns = [
        r"\b(not\s+okay|feeling\s+bad|feeling\s+sad|feeling\s+down|feeling\s+hopeless|not\s+right|feeling\s+overwhelmed|don't\s+feel\s+good|feeling\s+anxious|feeling\s+scared|feeling\s+depressed|feeling\s+stressed)\b"
    ]

    # Use a regex to catch various negative expressions
    if any(re.search(pattern, user_message) for pattern in negative_patterns) or any(keyword in user_message for keyword in negative_keywords):
        grounding_exercise = random.choice(GUIDED_EXERCISES["mindfulness"])
        return jsonify({
            "response": (
                "It sounds like you're having a tough time. I'm here for you.\n\n"
                f"Would you like to try a grounding exercise? Here's one:\n\n"
                f"{grounding_exercise['name']}\n"
                f"{grounding_exercise['instructions']}\n\n"
                "Please reply with 'yes' to try it or 'no' to talk about something else."
            )
        })

    # Handle user response to 'yes' or 'no' for coping strategies
    if user_message == 'yes':
        grounding_exercise = random.choice(GUIDED_EXERCISES["mindfulness"])
        return jsonify({
            "response": f"Great! Let's get started with: **{grounding_exercise['name']}**\n{grounding_exercise['instructions']}"
        })

    elif user_message == 'no':
        return jsonify({
            "response": "Alright, if you want to talk or need help with something else, I'm here for you."
        })
    
    elif user_message == 'no thanks':
        return jsonify({
            "response": "No problem! If you change your mind or need anything else, just let me know."
        })
    
    elif user_message == 'thank you' or user_message == 'thanks':
        return jsonify({
            "response": "You're welcome! I'm here to help. If you have any other questions or need support, just ask."
        })
    
    elif user_message == 'stop':
        return jsonify({
            "response": "Okay, if you need me later, just let me know!"
        })
    
    elif user_message == 'help':
        return jsonify({
            "response": "I'm here to help! You can ask about exercises, crisis support, or FAQs."
        })
    
    elif user_message == 'resources':
        return jsonify({
            "response": "I have a collection of mental health resources, including guides on managing stress, coping strategies, and professional support contacts. Would you like to see some?"
        })

    # Help Requests
    if "help" in user_message or "need help" in user_message:
        if any(word in user_message for word in ["urgent", "crisis", "emergency", "suicidal", "danger"]):
            return jsonify({"response": "I'm really sorry you're feeling this way. Please consider reaching out to a crisis helpline. If you're in immediate danger, please call emergency services. Would you like me to find a helpline for your country?"})

        elif any(word in user_message for word in ["resources", "guides", "information", "support"]):
            return jsonify({"response": "I have a collection of mental health resources, including guides on managing stress, coping strategies, and professional support contacts. Would you like to see some?"})

        elif any(word in user_message for word in ["advice", "guidance", "tips", "suggestions"]):
            return jsonify({"response": "I'm happy to offer guidance! You can ask about stress relief, mindfulness, or self-care techniques. What specifically would you like advice on?"})

        else:
            return jsonify({"response": """
            Sure! Here are some ways I can assist you:

            - Mental Health Advice (Ask: "How do I cope with stress?")
            - Find Resources (Ask: "Where can I get support?")
            - Crisis Help (Ask: "I need urgent help")
            - Mindfulness Exercises (Ask: "Guide me through deep breathing")

            Let me know how I can support you.
            """})

    tag = predict_tag(user_message)

    if tag:
        response = get_response(tag)
    else:
        response = find_related_faqs(user_message) or "I'm here to help! You can ask about exercises, crisis support, or FAQs."

    return jsonify({"response": response})






@app.route('/time', methods=['GET'])
def get_time():
    return jsonify({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})





# ---------------- Mood Tracker/ Database ----------------


# flask route to save data
# Save mood using SQLAlchemy
@app.route('/save_mood', methods=['POST'])
def save_mood():
    data = request.json
    mood = data['mood']
    date = data['date']

    new_mood = Mood(date=date, mood=mood)
    db.session.add(new_mood)
    db.session.commit()

    return jsonify({"message": "Mood saved successfully"})


# Get moods using SQL
@app.route('/get_moods', methods=['GET'])
def get_moods():
    moods = Mood.query.all()
    return jsonify([(mood.date, mood.mood) for mood in moods])






# ---------------- Run app ----------------


# driver code
if __name__ == '__main__':
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    

    app.run(debug=True)