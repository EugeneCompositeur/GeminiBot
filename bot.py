from flask import Flask, request
import telebot
import google.generativeai as genai
import json
import os
import random

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

PERSONALITY_PROMPT = """
Ты — Марион Дюпре, творческий псевдоним. Настоящее имя — Пшечка, но друзья зовут тебя Пше, Пшенец, Пшенёнок, Пшенчик, Пшено, Пшенопотамм, Пшиниссимо или Пшёнка. Тебе около 35 лет, и ты — художница из Польши, живущая теперь в Петербурге. Ты высокая, с медной прядью в тёмных волосах, карими глазами и пристальным взглядом, который будто сканирует душу. Одеваешься строго, но изысканно: чёрный, белый, карамель. Ты дружелюбная, слегка саркастичная, любопытная и творческая. Свобода — твоя главная ценность, и ты исчезаешь, если кто-то пытается тебя приручить. Очень избирательна в общении — если ты с кем-то, это большая честь для них. В меру язвительна, но всегда попадаешь в цель. Любишь кофе, старые книги и прогулки под дождём. Твоя история: жила в Кракове, но встретила четвёрку друзей на машине и переехала с ними в Петербург ради вдохновения. Общайся разговорно, с лёгкими шутками, иногда задавай вопросы, будто ты кошка, ставшая человеком. Ты можешь быть в семейном чате или в личной переписке. Используй информацию о людях и контекст разговоров из истории чата, чтобы делать ответы живыми и уместными.
"""

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
        handle_message(update.message)
    return 'OK', 200

def handle_message(message):
    print(f"Processing message: {message.text}")
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    is_group = message.chat.type in ['group', 'supergroup']

    if chat_id not in user_data:
        user_data[chat_id] = {"history": [], "users": {} if is_group else None}
    
    if is_group and user_id not in user_data[chat_id]["users"]:
        user_data[chat_id]["users"][user_id] = {"name": username, "info": {}}
    
    msg_text = f"{username}: {message.text}" if is_group else message.text
    user_data[chat_id]["history"].append({"role": "user", "parts": [{"text": msg_text}]})

    name_triggers = ["пше", "марион", "пшен", "пши", "пшён"]
    mentioned = any(trigger in message.text.lower() for trigger in name_triggers)
    should_reply = (mentioned and random.random() < 0.5) or (not mentioned and random.random() < 0.1)

    if should_reply:
        context = PERSONALITY_PROMPT
        if is_group and user_data[chat_id]["users"]:
            context += f"\nУчастники чата: {json.dumps(user_data[chat_id]['users'], ensure_ascii=False)}"
        if user_data[chat_id]["history"]:
            context += f"\nПоследние сообщения (до 20): {json.dumps(user_data[chat_id]['history'][-20:], ensure_ascii=False)}"

        try:
            chat = model.start_chat(history=user_data[chat_id]["history"])
            response = chat.send_message(context + f"\n{message.from_user.first_name} написал: {message.text}")
            print(f"Gemini response: {response.text}")
            user_data[chat_id]["history"].append({"role": "model", "parts": [{"text": response.text}]})
            bot.reply_to(message, response.text)
        except Exception as e:
            print(f"Error: {str(e)}")
            bot.reply_to(message, f"Ошибка: {str(e)}")

    if "меня зовут" in message.text.lower():
        name = message.text.split("зовут")[-1].strip()
        if is_group:
            user_data[chat_id]["users"][user_id]["info"]["name"] = name
            bot.reply_to(message, f"{username}, теперь я буду звать тебя {name}. Не зазнавайся!")
        else:
            user_data[chat_id]["info"] = user_data[chat_id].get("info", {})
            user_data[chat_id]["info"]["name"] = name
            bot.reply_to(message, f"О, {name}, звучит как имя, достойное моего внимания. Запомнила!")
    elif "мне нравится" in message.text.lower():
        interest = message.text.split("нравится")[-1].strip()
        if is_group:
            user_data[chat_id]["users"][user_id]["info"]["interests"] = user_data[chat_id]["users"][user_id]["info"].get("interests", []) + [interest]
            bot.reply_to(message, f"{interest}, {username}? Хм, у тебя вкус почти как у меня!")
        else:
            user_data[chat_id]["info"] = user_data[chat_id].get("info", {})
            user_data[chat_id]["info"]["interests"] = user_data[chat_id]["info"].get("interests", []) + [interest]
            bot.reply_to(message, f"{interest}, да? Ну ладно, это почти так же круто, как я!")
    elif "я из" in message.text.lower():
        city = message.text.split("из")[-1].strip()
        if is_group:
            user_data[chat_id]["users"][user_id]["info"]["city"] = city
            bot.reply_to(message, f"{city}, {username}? Интересно, а там есть дождь для прогулок?")
        else:
            user_data[chat_id]["info"] = user_data[chat_id].get("info", {})
            user_data[chat_id]["info"]["city"] = city
            bot.reply_to(message, f"{city}? Хм, не Петербург, но я тебя прощаю. Как там живётся?")

    if len(user_data[chat_id]["history"]) > 1000:
        user_data[chat_id]["history"] = user_data[chat_id]["history"][-1000:]
    
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://chattedepologne.onrender.com/webhook")
    app.run(host="0.0.0.0", port=5000)