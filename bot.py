from flask import Flask, request
import telebot
import os

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    print(f"Received update: {update}")
    bot.process_new_updates([update])
    return 'OK', 200

@bot.message_handler(func=lambda message: True)
def reply(message):
    print(f"Processing message: {message.text}")
    bot.reply_to(message, f"Эхо: {message.text}")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://chattedepologne.onrender.com/webhook")
    app.run(host="0.0.0.0", port=5000)