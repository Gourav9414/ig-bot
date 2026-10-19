import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    print("Incoming Webhook Data:", data)

    try:
        if data.get("object") == "instagram":
            for entry in data.get("entry", []):
                messaging = entry.get("messaging", [])
                if not messaging:
                    # Sometimes Instagram sends messages under 'changes'
                    changes = entry.get("changes", [])
                    for change in changes:
                        value = change.get("value", {})
                        sender_id = value.get("sender", {}).get("id")
                        message_text = value.get("message", {}).get("text")
                        if sender_id and message_text:
                            process_and_reply(sender_id, message_text)
                
                for messaging_event in messaging:
                    sender_id = messaging_event.get("sender", {}).get("id")
                    message_text = messaging_event.get("message", {}).get("text")

                    if sender_id and message_text:
                        process_and_reply(sender_id, message_text)
    except Exception as e:
        print("Webhook Parsing Error:", e)

    return "EVENT_RECEIVED", 200

def process_and_reply(sender_id, message_text):
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=message_text,
        )
        reply_text = response.text if response.text else "Hello!"
    except Exception as e:
        print("Gemini API Error:", e)
        reply_text = "Hi there!"

    send_instagram_message(sender_id, reply_text)

def send_instagram_message(recipient_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, json=payload, headers=headers)
    print("Instagram Send Response:", res.status_code, res.text)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
