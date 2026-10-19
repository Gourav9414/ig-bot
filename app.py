from flask import Flask, request
import requests
import google.generativeai as genai

app = Flask(__name__)

VERIFY_TOKEN = "my_custom_token_123"
GEMINI_API_KEY = "AQ.Ab8RN6K9tW6xNVqa6ZmCk72Ku1v9xWrcwvNSv81IMkj3iJKKLw"
ACCESS_TOKEN = "YOUR_INSTAGRAM_PAGE_ACCESS_TOKEN"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Invalid token", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        entry = data["entry"][0]["messaging"][0]
        sender_id = entry["sender"]["id"]
        message_text = entry["message"]["text"]

        prompt = f"Reply naturally in 1-2 sentences as an AI assistant on Instagram: {message_text}"
        ai_response = model.generate_content(prompt).text

        url = f"https://graph.facebook.com/v19.0/me/messages?access_token={ACCESS_TOKEN}"
        payload = {
            "recipient": {"id": sender_id},
            "message": {"text": ai_response}
        }
        requests.post(url, json=payload)
    except Exception as e:
        print("Error:", e)
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)