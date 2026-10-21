# -*- coding: utf-8 -*-
"""
BLACK STUDIO bot — Full Edition (telebot)
pip install -r requirements.txt
python bot_app.py
"""
import os
import json
import sqlite3
import random
import logging
from telebot import TeleBot, types

# ====================== CONFIG ======================
BOT_TOKEN = "8889779796:AAHlwmV3T6KB0_zi13UrRopG-XkI6zWlW_A"
ADMIN_ID = 8543358373                     # твой Telegram ID
OWNER_USERNAME = "@Evgenn010"              # куда покупатели отправляют звёзды
BOT_NAME = "BLACK STUDIO"

SUPPORT_URL = "https://t.me/blackstudio00"
REVIEWS_URL = "https://t.me/BlackSTUDIOotziv"
PAY_TEXT = f"Для оплаты переведите нужную сумму на [@Evgenn010]({OWNER_USERNAME}) и отправьте скриншот в поддержку."

SETTINGS_FILE = "settings.json"
IMG = "images"
LINE = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
# ====================================================

logging.basicConfig(level=logging.INFO)
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- DATABASE SETUP ---
db = sqlite3.connect("black_studio.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    balance INTEGER DEFAULT 0,
    comp_limit INTEGER DEFAULT 3,
    ref_by INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS promo (
    code TEXT PRIMARY KEY,
    reward INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS used_promo (
    user_id INTEGER,
    code TEXT
)
""")
db.commit()

def get_user(uid, name="User"):
    cursor.execute("SELECT id, balance, comp_limit FROM users WHERE id = ?", (uid,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (id, name) VALUES (?, ?)", (uid, name))
        db.commit()
        return (uid, 0, 3)
    return row

def is_admin(uid):
    return uid == ADMIN_ID

def menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🔥 Бесплатный проект"),
        types.KeyboardButton("⚡ Купить MOD ULTRA"),
        types.KeyboardButton("📊 Приобрести рекламу"),
        types.KeyboardButton("📍 Предложить слив"),
        types.KeyboardButton("🎁 Промокод"),
        types.KeyboardButton("👥 Пригласить друзей"),
        types.KeyboardButton("🔨 Компиляция"),
        types.KeyboardButton("🎰 Рулетка"),
        types.KeyboardButton("⚙️ Поддержка и Отзывы")
    )
    if is_admin(uid):
        markup.add(types.KeyboardButton("🛠 Админ-панель"))
    return markup

def head(emoji, title):
    return f"{emoji} <b>{title}</b>\n{LINE}\n\n"

# --- HANDLERS: START ---
@bot.message_handler(commands=["start"])
def start_cmd(m: types.Message):
    u = m.from_user
    args = m.text.split()
    get_user(u.id, u.first_name)
    
    # Реферальная система
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != u.id:
            cursor.execute("SELECT ref_by FROM users WHERE id = ?", (u.id,))
            res = cursor.fetchone()
            if res and not res[0]:
                cursor.execute("UPDATE users SET ref_by = ? WHERE id = ?", (ref_id, u.id))
                cursor.execute("UPDATE users SET balance = balance + 5 WHERE id = ?", (ref_id,))
                db.commit()
                try:
                    bot.send_message(ref_id, f"🎉 По вашей ссылке зарегистрировался новый пользователь! Вам начислено <b>+5 монет</b>.")
                except:
                    pass

    text = (
        head("🖐", f"Добро пожаловать в {BOT_NAME}!") +
        f"Лучшая студия скриптинга, разработки и игровых сборок.\n\n"
        f"▫️ Выбирайте нужные разделы в меню ниже.\n"
        f"▫️ По всем вопросам: {OWNER_USERNAME}\n\n" + LINE
    )
    bot.send_message(m.chat.id, text, reply_markup=menu(u.id))

# --- MAIN MENU ROUTING ---
@bot.message_handler(func=lambda m: True)
def main_router(m: types.Message):
    uid = m.from_user.id
    text = m.text
    get_user(uid, m.from_user.first_name)

    if text == "🔥 Бесплатный проект":
        msg = (
            head("🔥", "Бесплатные проекты") +
            "Здесь вы можете скачать готовые сливы серверов, моды и базы данных абсолютно бесплатно!\n\n"
            f"📢 Наш канал с проектами: {SUPPORT_URL}\n"
            f"💬 Отзывы клиентов: {REVIEWS_URL}"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "⚡ Купить MOD ULTRA":
        msg = (
            head("⚡", "MOD ULTRA (Привилегия)") +
            "Получите максимальные возможности, скрытые функции и эксклюзивные скрипты.\n\n"
            "💰 <b>Цена:</b> 149 ₽ / 50 Telegram Stars\n\n"
            f"{PAY_TEXT}"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "📊 Приобрести рекламу":
        msg = (
            head("📊", "Реклама в проектах") +
            "Хотите прорекламировать свой сервер или проект?\n\n"
            "📌 Рассылка по ботам и каналам сети.\n"
            f"💬 Пишите владельцу для заказа: {OWNER_USERNAME}"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "📍 Предложить слив":
        msg = (
            head("📍", "Предложить слив / мод") +
            f"Есть крутой слив или скрипт? Присылайте материал напрямую владельцу: {OWNER_USERNAME}. Лучшие работы публикуем с указанием автора!"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "🎁 Промокод":
        msg = bot.send_message(m.chat.id, "🎁 Введите ваш промокод в ответном сообщении:")
        bot.register_next_step_handler(msg, process_promo)

    elif text == "👥 Пригласить друзей":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={uid}"
        msg = (
            head("👥", "Реферальная система") +
            "Приглашайте друзей по вашей личной ссылке и получайте бонусы!\n\n"
            f"🔗 Ваша ссылка:\n<code>{ref_link}</code>\n\n"
            "💰 За каждого приглашенного друга начисляется бонус на баланс."
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "🔨 Компиляция":
        cursor.execute("SELECT comp_limit FROM users WHERE id = ?", (uid,))
        limit = cursor.fetchone()[0]
        msg = (
            head("🔨", "Облачная компиляция Pawn") +
            f"У вас осталось бесплатных компиляций: <b>{limit}</b>\n\n"
            "Отправьте ваш `.pwn` файл скрипта сюда в чат, и бот скомпилирует его для вас!"
        )
        if limit > 0:
            bot.send_message(m.chat.id, msg, reply_markup=menu(uid))
            bot.register_next_step_handler(bot.send_message(m.chat.id, "📤 Прикрепите `.pwn` файл:"), process_compilation)
        else:
            bot.send_message(m.chat.id, "❌ У вас закончились бесплатные компиляции!", reply_markup=menu(uid))

    elif text == "🎰 Рулетка":
        msg = (
            head("🎰", "Ежедневная рулетка") +
            "Испытайте удачу! Вы можете выиграть бесплатные компиляции или бонусные баллы."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎲 Крутить рулетку", callback_data="spin_roulette"))
        bot.send_message(m.chat.id, msg, reply_markup=markup)

    elif text == "⚙️ Поддержка и Отзывы":
        msg = (
            head("⚙️", "Информация") +
            f"🛠 <b>Поддержка:</b> {SUPPORT_URL}\n"
            f"💬 <b>Отзывы:</b> {REVIEWS_URL}\n"
            f"👑 <b>Владелец:</b> {OWNER_USERNAME}"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "🛠 Админ-панель" and is_admin(uid):
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        msg = (
            head("🛠", "Панель администратора") +
            f"👥 Всего пользователей в базе: <b>{users_count}</b>\n\n"
            "Выберите действие:"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
            types.InlineKeyboardButton("➕ Создать промо", callback_data="admin_addpromo")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

# --- PROMOCODE LOGIC ---
def process_promo(m: types.Message):
    uid = m.from_user.id
    code = m.text.strip()
    cursor.execute("SELECT reward FROM promo WHERE code = ?", (code,))
    promo = cursor.fetchone()
    if not promo:
        bot.send_message(m.chat.id, "❌ Неверный промокод!", reply_markup=menu(uid))
        return

    cursor.execute("SELECT * FROM used_promo WHERE user_id = ? AND code = ?", (uid, code))
    if cursor.fetchone():
        bot.send_message(m.chat.id, "⚠️ Вы уже активировали этот промокод!", reply_markup=menu(uid))
        return

    reward = promo[0]
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (reward, uid))
    cursor.execute("INSERT INTO used_promo (user_id, code) VALUES (?, ?)", (uid, code))
    db.commit()
    bot.send_message(m.chat.id, f"✅ Промокод успешно активирован! Начислено: <b>+{reward} баллов</b>.", reply_markup=menu(uid))

# --- COMPILATION LOGIC WITH LIMITS ---
def process_compilation(m: types.Message):
    uid = m.from_user.id
    if not m.document or not m.document.file_name.endswith(".pwn"):
        bot.send_message(m.chat.id, "❌ Пожалуйста, отправьте именно `.pwn` файл документом.", reply_markup=menu(uid))
        return

    cursor.execute("SELECT comp_limit FROM users WHERE id = ?", (uid,))
    limit = cursor.fetchone()[0]
    if limit <= 0:
        bot.send_message(m.chat.id, "❌ Превышен лимит компиляций!", reply_markup=menu(uid))
        return

    cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
    db.commit()

    bot.send_message(m.chat.id, "⚙️ Скрипт принят в очередь на компиляцию... Пожалуйста, подождите.")
    import time
    time.sleep(2)
    bot.send_message(m.chat.id, f"✅ <b>Компиляция успешно завершена!</b>\nОсталось лимита: {limit - 1}", reply_markup=menu(uid))

# --- CALLBACKS (ROULETTE & ADMIN) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call: types.CallbackQuery):
    uid = call.from_user.id
    data = call.data

    if data == "spin_roulette":
        reward = random.choice([1, 2, 3, 0, 5])
        if reward > 0:
            cursor.execute("UPDATE users SET comp_limit = comp_limit + ? WHERE id = ?", (reward, uid))
            db.commit()
            bot.answer_callback_query(call.id, f"🎉 Поздравляем! Вы выиграли +{reward} к лимиту компиляций!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "😢 В этот раз ничего не выпало. Попробуйте завтра!", show_alert=True)

    elif data == "admin_addpromo" and is_admin(uid):
        msg = bot.send_message(call.message.chat.id, "Введите промокод и награду через пробел (например: <code>BLACK 5</code>):")
        bot.register_next_step_handler(msg, save_new_promo)

    elif data == "admin_broadcast" and is_admin(uid):
        msg = bot.send_message(call.message.chat.id, "Введите текст для рассылки всем пользователям:")
        bot.register_next_step_handler(msg, execute_broadcast)

def save_new_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code = parts[0]
        reward = int(parts[1])
        cursor.execute("INSERT OR REPLACE INTO promo (code, reward) VALUES (?, ?)", (code, reward))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> на {reward} баллов успешно создан!")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>BLACK 3</code>")

def execute_broadcast(m: types.Message):
    text = m.text
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    success = 0
    for u in users:
        try:
            bot.send_message(u[0], f"📢 <b>Рассылка от Black Studio:</b>\n\n{text}")
            success += 1
        except:
            pass
    bot.send_message(m.chat.id, f"✅ Рассылка завершена. Успешно отправлено: {success} пользователям.")

if __name__ == "__main__":
    print("BLACK STUDIO bot успешно запущен!")
    bot.infinity_polling(skip_pending=True)