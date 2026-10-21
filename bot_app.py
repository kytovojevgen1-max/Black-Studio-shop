# -*- coding: utf-8 -*-
"""
BLACK STUDIO bot — pyTelegramBotAPI (telebot)
pip install -r requirements.txt
python bot_app.py
"""
import os
import json
import sqlite3
import time
import logging
from telebot import TeleBot, types

# ====================== CONFIG ======================
BOT_TOKEN = "8889779796:AAHlwmV3T6KB0_zi13UrRopG-XkI6zWlW_A"
ADMIN_ID = 8543358373                     # твой Telegram ID
OWNER_USERNAME = "@Evgenn010"              # куда покупатели отправляют звёзды
BOT_NAME = "BLACK STUDIO"

SUPPORT_URL = "https://t.me/d3v_nexus"
REVIEWS_URL = "https://t.me/reps_nexus"
PAY_TEXT = "Переведи сумму <code>t.me/Evgenn010</code> и ожидайте сообщения"

SETTINGS_FILE = "settings.json"
IMG = "images"
LINE = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
# ====================================================

logging.basicConfig(level=logging.INFO)
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

SET = {"pay_text": PAY_TEXT, "support": SUPPORT_URL, "reviews": REVIEWS_URL, "owner": OWNER_USERNAME, "admins": []}
SET.update(load_json(SETTINGS_FILE, {}))

db = sqlite3.connect("nexus.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, premium INTEGER DEFAULT 0,"
           "mod INTEGER, sql INTEGER, adm INTEGER, conv INTEGER, apk INTEGER)")
db.commit()

def is_admin(uid):
    return uid == ADMIN_ID or uid in SET.get("admins", [])

def menu(uid=None):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton(text="🔥 Бесплатный проект"))
    markup.row(types.KeyboardButton(text="📊 Приобрести рекламу"), types.KeyboardButton(text="📍 Предложить слив"))
    markup.row(types.KeyboardButton(text="⚡ Купить MOD ULTRA"), types.KeyboardButton(text="🔧 Разработка"))
    markup.row(types.KeyboardButton(text="🎁 Промокод"), types.KeyboardButton(text="👥 Пригласить друзей"))
    markup.row(types.KeyboardButton(text="🔨 Компиляция"), types.KeyboardButton(text="🎰 Рулетка"))
    if is_admin(uid):
        markup.row(types.KeyboardButton(text="🛠 Админ-панель"))
    return markup

def head(emoji, title):
    return f"{emoji} <b>{title}</b>\n{LINE}\n\n"

@bot.message_handler(commands=["start"])
@bot.message_handler(func=lambda m: m.text == "Главное меню")
def start_command(m: types.Message):
    u = m.from_user
    text = (head("🖐", f"Здравствуйте, {u.full_name}!") + f"Что умеет {BOT_NAME} SHOP:\n\n"
            "🔥 Бесплатный проект\n⚡ Купить MOD ULTRA\n❤️ Приобрести рекламу\n"
            "⚠️ Поддержка — в разделе «Помощь»\n✅ Отзывы — после получения APK\n\n" + LINE + "\n\n<i>Выбери раздел в меню ниже</i>")
    
    path = os.path.join(IMG, "main.jpg")
    if os.path.exists(path):
        with open(path, "rb") as photo:
            bot.send_photo(m.chat.id, photo, caption=text, reply_markup=menu(u.id))
    else:
        bot.send_message(m.chat.id, text, reply_markup=menu(u.id))

@bot.message_handler(func=lambda m: True)
def handle_all(m: types.Message):
    if m.text == "🛠 Админ-панель" and is_admin(m.from_user.id):
        bot.send_message(m.chat.id, "🛠 <b>Панель администратора активна.</b>", reply_markup=menu(m.from_user.id))
        return
    bot.send_message(m.chat.id, "Выбери нужный раздел в меню ниже:", reply_markup=menu(m.from_user.id))

if __name__ == "__main__":
    print("Бот успешно запущен на telebot!")
    bot.infinity_polling(skip_pending=True)
    
