from flask import Flask, request
import telebot
import google.generativeai as genai
import json
import os

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

try:
    with open("user_data.json", "r") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    print(f"Received update: {update}")
    if update.message:
        reply(update.message)
    return 'OK', 200

def reply(message):
    print(f"Processing message: {message.text}")
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = []
    user_data[user_id].append({"role": "user", "content": message.text})
    try:
        chat = model.start_chat(history=user_data[user_id])
        response = chat.send_message(message.text)
        print(f"Gemini response: {response.text}")
        user_data[user_id].append({"role": "model", "content": response.text})
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {str(e)}")
        bot.reply_to(message, f"Ошибка: {str(e)}")
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://chattedepologne.onrender.com/webhook")
    app.run(host="0.0.0.0", port=5000)