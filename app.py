from flask import Flask, render_template, request, jsonify
import datetime

app = Flask(__name__)

# Example data for FAQ and resources
FAQ = [
    {"question": "What is mental health?", "answer": "Mental health includes our emotional, psychological, and social well-being. It affects how we think, feel, and act."},
    {"question": "How can I manage stress?", "answer": "You can manage stress by exercising, practicing mindfulness, staying organized, and seeking support from friends or professionals."}
]

CRISIS_HELPLINES = [
    {"name": "National Suicide Prevention Lifeline", "number": "1-800-273-TALK"},
    {"name": "Crisis Text Line", "text": "Text HOME to 741741"}
]

GUIDED_EXERCISES = {
    "mindfulness": "Take a moment to sit comfortably and focus on your breath. Inhale deeply through your nose for 4 seconds, hold for 4 seconds, and exhale through your mouth for 4 seconds. Repeat for 5 minutes.",
    "breathing": "Try the 4-7-8 technique: Breathe in through your nose for 4 seconds, hold your breath for 7 seconds, and exhale slowly through your mouth for 8 seconds. Repeat 4 times."
}

@app.route('/')
def home():
    return render_template('index.html')  # Placeholder HTML for the chatbot interface

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').lower()
    response = ""

    if "help" in user_message or "crisis" in user_message:
        response = "Here are some crisis helplines:\n" + "\n".join([f"{line['name']}: {line.get('number', line.get('text'))}" for line in CRISIS_HELPLINES])
    elif "exercise" in user_message or "mindfulness" in user_message:
        response = GUIDED_EXERCISES.get("mindfulness", "Let's take a mindful moment.")
    elif "breathing" in user_message:
        response = GUIDED_EXERCISES.get("breathing", "Let's focus on our breathing.")
    elif "faq" in user_message:
        response = "Here are some frequently asked questions:\n" + "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in FAQ])
    else:
        response = "I'm here to help! You can ask about exercises, crisis support, or FAQs."

    return jsonify({"response": response})

@app.route('/time', methods=['GET'])
def get_time():
    return jsonify({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

if __name__ == '__main__':
    app.run(debug=True)
