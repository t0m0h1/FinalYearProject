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

# Create user model (class user)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)


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

    return render_template('login_signup.html')



# Route for logging in
@app.route('/login', methods=['POST'])
def login():
    # Debugging: Print when the route is hit
    print("Login POST request received")

    # Ensure request contains JSON data
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Handle missing data
        if not email or not password:
            return jsonify({'message': 'Email and password are required!'}), 400

        # Fetch the user from the database
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            # Successful login
            login_user(user)
            flash('Login successful!', category='success')
            print(f"User authenticated: {current_user.is_authenticated}")

            return jsonify({
                'message': 'Login successful!',
                'redirect': url_for('home')  # Assuming 'home' is a defined route
            })
        else:
            flash('Invalid credentials, try again.', category='error')
            return jsonify({'message': 'Invalid credentials, try again.'}), 401
    else:
        return jsonify({'message': 'Request must be JSON!'}), 400






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



# ---------------- Routes ----------------


# Routes - these are the functions the app will respond to
@app.route('/')
@login_required # This will redirect to the login page if the user is not logged in
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

# Get moods using SQLAlchemy
@app.route('/get_moods', methods=['GET'])
def get_moods():
    moods = Mood.query.all()
    return jsonify([(mood.date, mood.mood) for mood in moods])

# Define Mood model
class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100))
    mood = db.Column(db.String(50))




# ---------------- Run app ----------------


# driver code
if __name__ == '__main__':
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    

    app.run(debug=True)