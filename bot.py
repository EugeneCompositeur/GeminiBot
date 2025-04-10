from flask import Flask, request
import telebot
import google.generativeai as genai
import json
import os

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv("7542475591:AAGaUekkP7oUgWcOpkf6uNlcVUQe0KSh9Lc"))  # Берем токен из переменной окружения

genai.configure(api_key=os.getenv("AIzaSyBOna2ZOyqivhD2b_saoi6fHc6_N4phpiU"))  # Берем ключ из переменной окружения
model = genai.GenerativeModel("gemini-1.5-flash")

try:
    with open("user_data.json", "r") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'OK', 200

@bot.message_handler(func=lambda message: True)
def reply(message):
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = []
    user_data[user_id].append({"role": "user", "content": message.text})
    try:
        chat = model.start_chat(history=user_data[user_id])
        response = chat.send_message(message.text)
        user_data[user_id].append({"role": "model", "content": response.text})
        bot.reply_to(message, response.text)  # Отправляем ответ пользователю
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")  # Сообщаем об ошибке
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://chattedepologne.onrender.com/webhook")
    app.run(host="0.0.0.0", port=5000)