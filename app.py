import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Load Environment Variables from Render
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route('/', methods=['GET'])
def home():
    return "Bot is running live!"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Forbidden', 403
    return 'Bad Request', 400

@app.route('/webhook', methods=['POST'])
def webhook_event():
    data = request.get_json()

    if data.get("object") == "instagram":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                message_text = messaging_event.get("message", {}).get("text")

                if sender_id and message_text:
                    try:
                        # Generate AI response using Gemini
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=message_text,
                        )
                        reply_text = response.text if response.text else "Sorry, I couldn't process that."
                    except Exception as e:
                        print("Gemini API Error:", e)
                        reply_text = "Sorry, I am having trouble responding right now."

                    # Send reply back to Instagram DM
                    send_instagram_message(sender_id, reply_text)

    return "EVENT_RECEIVED", 200

def send_instagram_message(recipient_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
