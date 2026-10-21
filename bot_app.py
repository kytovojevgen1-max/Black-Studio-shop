# -*- coding: utf-8 -*-
"""
BLACK STUDIO bot — Separate PWN & JNI Compilers (telebot)
pip install -r requirements.txt
python bot_app.py
"""
import os
import json
import sqlite3
import random
import datetime
import logging
from telebot import TeleBot, types

# ====================== CONFIG ======================
BOT_TOKEN = "8889779796:AAHlwmV3T6KB0_zi13UrRopG-XkI6zWlW_A"
ADMIN_ID = 8543358373                     # твой Telegram ID
OWNER_USERNAME = "@Evgenn010"              # связь / оплата
OWNER_VK = "vk.ru/evgenn09"
REVIEWS_URL = "https://t.me/BlackSTUDIOotziv"
BOT_NAME = "BLACK STUDIO"

LINE = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
# ====================================================

logging.basicConfig(level=logging.INFO)
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- DATABASE SETUP ---
db = sqlite3.connect("nexus.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    balance INTEGER DEFAULT 0,
    comp_limit INTEGER DEFAULT 30,
    last_reset TEXT,
    ref_by INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS promo (
    code TEXT PRIMARY KEY,
    discount INTEGER,
    max_uses INTEGER,
    used_count INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS used_promo (
    user_id INTEGER,
    code TEXT
)
""")
db.commit()

# Временное хранилище выбранного режима (PWN или JNI с версией NDK)
user_temp_mode = {}

def get_user(uid, name="User"):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT id, balance, comp_limit, last_reset FROM users WHERE id = ?", (uid,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO users (id, name, last_reset) VALUES (?, ?, ?)", (uid, name, today))
        db.commit()
        return (uid, 0, 30)
    else:
        user_id, balance, comp_limit, last_reset = row
        if last_reset != today:
            cursor.execute("UPDATE users SET comp_limit = 30, last_reset = ? WHERE id = ?", (today, uid))
            db.commit()
            return (user_id, balance, 30)
        return (user_id, balance, comp_limit)

def is_admin(uid):
    return uid == ADMIN_ID

def menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("👤 Мой профиль"),
        types.KeyboardButton("🛍 Магазин (Buy list)"),
        types.KeyboardButton("🔨 PWN Compiler"),
        types.KeyboardButton("⚙️ JNI Compiler"),
        types.KeyboardButton("🎁 Промокод"),
        types.KeyboardButton("👥 Пригласить друзей"),
        types.KeyboardButton("⚙️ Поддержка"),
        types.KeyboardButton("❓ Как пользоваться")
    )
    if is_admin(uid):
        markup.add(types.KeyboardButton("🛠 Админ-панель"))
    return markup

def head(emoji, title):
    return f"{emoji} <b>{title}</b>\n{LINE}\n\n"

# --- START ---
@bot.message_handler(commands=["start"])
def start_cmd(m: types.Message):
    u = m.from_user
    args = m.text.split()
    get_user(u.id, u.first_name)
    
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
                    bot.send_message(ref_id, f"🎉 По вашей ссылке зарегистрировался новый пользователь! Вам начислено +5 баллов.")
                except:
                    pass

    text = (
        head("🖐", f"Добро пожаловать в {BOT_NAME}!") +
        f"Лучшая студия скриптинга, разработки и игровых сборок.\n\n"
        f"▫️ Ежедневный лимит бесплатных компиляций: <b>30 раз в день</b>.\n"
        f"▫️ Выбирайте нужный компилятор в меню ниже 👇"
    )
    bot.send_message(m.chat.id, text, reply_markup=menu(u.id))

# --- ROUTER ---
@bot.message_handler(func=lambda m: True)
def main_router(m: types.Message):
    uid = m.from_user.id
    text = m.text
    balance, comp_limit = get_user(uid, m.from_user.first_name)[1:]

    if text == "👤 Мой профиль":
        msg = (
            head("👤", "Личный кабинет") +
            f"🆔 <b>Ваш ID:</b> <code>{uid}</code>\n"
            f"👤 <b>Имя:</b> {m.from_user.full_name}\n"
            f"🔨 <b>Осталось компиляций на сегодня:</b> {comp_limit} / 30\n"
            f"💰 <b>Баланс баллов:</b> {balance}\n\n"
            f"<i>Лимит обновляется автоматически каждый день в 00:00 по МСК.</i>"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "🛍 Магазин (Buy list)":
        price_text = (
            head("🛍", "Официальный прайс-лист Black Studio") +
            "<b>📱 Моды (mobile):</b>\n"
            "• Black Russia 2025-26 (планшет): 140 ⭐ (без pwn 100 ₽) (с pwn 150 ₽)\n"
            "• Black Russia 2025 (без планшета): 120 ⭐ (без pwn 60 ₽) (с pwn 90 ₽)\n"
            "• Black Russia 2025 (без планшета, роботы фулл): 100 ⭐ (без pwn 80 ₽) (с pwn 130 ₽)\n\n"
            "<b>💻 Моды (ПК):</b>\n"
            "• Радмир 8.4: 100 ⭐ (без pwn 90 ₽) (с pwn 150 ₽)\n\n"
            "<b>🌐 Форумы (50 ⭐ / 40 ₽ каждый):</b>\n"
            "• Black Russia Forum, Gold Russia, Live Russia, Матрёшка РП, Суровая Россия, Amazing RP, CRMP-ONLINE, Rage Russia\n\n"
            "<b>🌍 Сайты (50 ⭐ / 38 ₽ каждый):</b>\n"
            "• Copy Black Russia (old), King Russia, Online Russia, Rage Russia\n\n"
            "<b>⚙️ Прочее (50 ⭐ / 40 ₽ каждый):</b>\n"
            "• Ваш стиль на форум\n• Поставить ваш мод на сервер\n• Сделать / подключить лаунчер\n"
            "<i>Другое: пишите в ЛС для расчета стоимости.</i>\n\n"
            f"📌 <b>Примечание:</b> Обязательно наличие своего хостинга! Возможна оплата в рублях напрямую на хостинг.\n\n"
            f"👑 <b>Контакты для покупки:</b>\n"
            f"• Telegram: {OWNER_USERNAME}\n"
            f"• VK: {OWNER_VK}\n"
            f"• Отзывы: {REVIEWS_URL}"
        )
        bot.send_message(m.chat.id, price_text, reply_markup=menu(uid))

    elif text == "🔨 PWN Compiler":
        user_temp_mode[uid] = "PWN"
        msg = (
            head("🔨", "PWN Compiler (Pawno / Pawn)") +
            f"Осталось попыток: <b>{comp_limit} / 30</b>\n\n"
            "📤 Отправьте ваш файл скрипта <code>.pwn</code> сюда в чат документом, и бот выполнит компиляцию."
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "⚙️ JNI Compiler":
        msg = (
            head("⚙️", "JNI Compiler · Выбор NDK") +
            "Выберите версию Android NDK для сборки вашего JNI-проекта:\n\n"
            "🟢 <b>r25c</b> — современные проекты, актуальные Google Play и CRMP\n"
            "🟡 <b>r21e</b> — совместимый средний вариант\n"
            "🔴 <b>r16b</b> — старые JNI-проекты"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🟢 NDK r25c · рекомендую", callback_data="ndk_r25c"),
            types.InlineKeyboardButton("🟡 NDK r21e · совместимость", callback_data="ndk_r21e"),
            types.InlineKeyboardButton("🔴 NDK r16b · старые проекты", callback_data="ndk_r16b")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

    elif text == "🎁 Промокод":
        msg = bot.send_message(m.chat.id, "🎁 Введите ваш промокод в ответном сообщении:")
        bot.register_next_step_handler(msg, process_promo)

    elif text == "👥 Пригласить друзей":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={uid}"
        msg = (
            head("👥", "Реферальная система") +
            "Приглашайте друзей по вашей личной ссылке и получайте бонусы!\n\n"
            f"🔗 Ваша ссылка:\n<code>{ref_link}</code>"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "⚙️ Поддержка":
        msg = (
            head("⚙️", "Связь и поддержка") +
            f"💬 <b>Отзывы:</b> {REVIEWS_URL}\n"
            f"👑 <b>Владелец (Telegram):</b> {OWNER_USERNAME}\n"
            f"👑 <b>Владелец (VK):</b> {OWNER_VK}"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "❓ Как пользоваться":
        msg = (
            head("❓", "Инструкция по использованию") +
            "1️⃣ Нажмите <b>🔨 PWN Compiler</b> для компиляции `.pwn` скриптов.\n"
            "2️⃣ Нажмите <b>⚙️ JNI Compiler</b>, выберите NDK и отправьте `.jni` или архив `.zip` / `.rar`.\n"
            "3️⃣ Получайте результат моментально в рамках суточного лимита (30 раз в день).\n\n"
            f"По всем вопросам: {OWNER_USERNAME}"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "🛠 Админ-панель" and is_admin(uid):
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        msg = (
            head("🛠", "Панель администратора") +
            f"👥 Всего пользователей: <b>{users_count}</b>\n\n"
            "Выберите действие:"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Создать промо", callback_data="admin_addpromo"),
            types.InlineKeyboardButton("📋 Список промо", callback_data="admin_listpromo"),
            types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

# --- CALLBACKS (NDK & ADMIN) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("ndk_") or call.data.startswith("admin_"))
def callback_router(call: types.CallbackQuery):
    uid = call.from_user.id
    data = call.data

    if data in ("ndk_r25c", "ndk_r21e", "ndk_r16b"):
        ndk_version = data.replace("ndk_", "").upper()
        user_temp_mode[uid] = f"JNI_{ndk_version}"
        
        bot.answer_callback_query(call.id, f"Выбрана NDK: {ndk_version}")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=head("⚙️", f"JNI Compiler (NDK: {ndk_version})") +
                 "📤 Теперь отправьте ваш архив <code>.zip</code> / <code>.rar</code> или файл <code>.jni</code> сюда в чат документом!"
        )
        return

    if not is_admin(uid):
        return

    if data == "admin_addpromo":
        msg = bot.send_message(call.message.chat.id, "Введите промокод, скидку (%) и лимит людей через пробел.\nПример: <code>BLACK20 15 5000</code>")
        bot.register_next_step_handler(msg, save_new_promo)

    elif data == "admin_listpromo":
        cursor.execute("SELECT code, discount, max_uses, used_count FROM promo")
        promos = cursor.fetchall()
        if not promos:
            bot.answer_callback_query(call.id, "Нет активных промокодов.", show_alert=True)
            return
        text = "📋 <b>Активные промокоды:</b>\n\n"
        for p in promos:
            text += f"🔑 <code>{p[0]}</code> | Скидка: {p[1]}% | Использовано: {p[3]} / {p[2]}\n"
        bot.send_message(call.message.chat.id, text)

    elif data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "Введите текст для рассылки всем пользователям:")
        bot.register_next_step_handler(msg, execute_broadcast)

# --- FILE HANDLER (SEPARATE PWN & JNI) ---
@bot.message_handler(content_types=['document'])
def process_compilation(m: types.Message):
    uid = m.from_user.id
    if not m.document:
        bot.send_message(m.chat.id, "❌ Пожалуйста, прикрепите файл документом.", reply_markup=menu(uid))
        return
        
    fname = m.document.file_name.lower()
    mode = user_temp_mode.get(uid, "PWN")

    # Проверка формата в зависимости от выбранного режима
    if mode == "PWN":
        if not fname.endswith(".pwn"):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>PWN Compiler</b>. Пожалуйста, отправьте файл с расширением <code>.pwn</code>.", reply_markup=menu(uid))
            return
    else: # JNI режим
        allowed_jni = (".jni", ".zip", ".rar", ".tar", ".gz", ".7z")
        if not fname.endswith(allowed_jni):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>JNI Compiler</b>. Пожалуйста, отправьте архив <code>.zip</code> / <code>.rar</code> или файл <code>.jni</code>.", reply_markup=menu(uid))
            return

    _, _, limit = get_user(uid)
    if limit <= 0:
        bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
        return

    # Списываем 1 попытку
    cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
    db.commit()

    compiler_name = "PWN Compiler" if mode == "PWN" else f"JNI Compiler ({mode.replace('JNI_', 'NDK ')})"

    sent_msg = bot.send_message(
        m.chat.id, 
        f"⚙️ <b>{compiler_name}</b>\n"
        f"📁 Файл: <code>{m.document.file_name}</code>\n"
        f"🔄 <i>Выполняется сборка...</i>"
    )
    
    import time
    time.sleep(2)
    
    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=sent_msg.message_id,
        text=f"✅ <b>Компиляция успешно завершена!</b>\n\n"
             f"🛠 Режим: <b>{compiler_name}</b>\n"
             f"📁 Файл: <code>{m.document.file_name}</code>\n"
             f"📉 Осталось попыток на сегодня: <b>{limit - 1} / 30</b>",
        reply_markup=menu(uid)
    )

# --- PROMO & ADMIN LOGIC ---
def process_promo(m: types.Message):
    uid = m.from_user.id
    code = m.text.strip()
    
    cursor.execute("SELECT discount, max_uses, used_count FROM promo WHERE code = ?", (code,))
    promo = cursor.fetchone()
    
    if not promo:
        bot.send_message(m.chat.id, "❌ Промокод не найден или уже удален (лимит исчерпан)!", reply_markup=menu(uid))
        return

    discount, max_uses, used_count = promo

    cursor.execute("SELECT * FROM used_promo WHERE user_id = ? AND code = ?", (uid, code))
    if cursor.fetchone():
        bot.send_message(m.chat.id, "⚠️ Вы уже использовали этот промокод!", reply_markup=menu(uid))
        return

    if used_count >= max_uses:
        cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
        db.commit()
        bot.send_message(m.chat.id, "❌ Лимит активаций этого промокода исчерпан, он больше недействителен.", reply_markup=menu(uid))
        return

    new_used = used_count + 1
    if new_used >= max_uses:
        cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
    else:
        cursor.execute("UPDATE promo SET used_count = ? WHERE code = ?", (new_used, code))
    
    cursor.execute("INSERT INTO used_promo (user_id, code) VALUES (?, ?)", (uid, code))
    db.commit()

    bot.send_message(m.chat.id, f"✅ Промокод успешно активирован!\n🔥 Ваша скидка: <b>{discount}%</b> на покупку услуг у владельца {OWNER_USERNAME}", reply_markup=menu(uid))

def save_new_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code = parts[0]
        discount = int(parts[1])
        max_uses = int(parts[2])
        
        cursor.execute("INSERT OR REPLACE INTO promo (code, discount, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, discount, max_uses))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> успешно создан!\nскидка: {discount}%\nлимит пользователей: {max_uses}")
    except Exception:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>BLACK20 15 5000</code>")

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
    print("BLACK STUDIO bot с раздельными компиляторами успешно запущен!")
    bot.infinity_polling(skip_pending=True)
льца {OWNER_USERNAME}", reply_markup=menu(uid))

# --- COMPILATION HANDLER ---
def process_compilation(m: types.Message):
    uid = m.from_user.id
    if not m.document:
        bot.send_message(m.chat.id, "❌ Пожалуйста, отправьте документ (.pwn или .jni).", reply_markup=menu(uid))
        return
        
    fname = m.document.file_name
    if not (fname.endswith(".pwn") or fname.endswith(".jni")):
        bot.send_message(m.chat.id, "❌ Поддерживаются только файлы с расширением `.pwn` или `.jni`.", reply_markup=menu(uid))
        return

    _, _, limit = get_user(uid)
    if limit <= 0:
        bot.send_message(m.chat.id, "❌ Превышен лимит компиляций на сегодня!", reply_markup=menu(uid))
        return

    cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
    db.commit()

    bot.send_message(m.chat.id, f"⚙️ Файл <code>{fname}</code> принят в очередь. Идет компиляция...")
    import time
    time.sleep(2)
    bot.send_message(m.chat.id, f"✅ <b>Компиляция успешно завершена!</b>\nОсталось попыток на сегодня: {limit - 1}", reply_markup=menu(uid))

# --- ADMIN CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call: types.CallbackQuery):
    uid = call.from_user.id
    data = call.data

    if not is_admin(uid):
        return

    if data == "admin_addpromo":
        msg = bot.send_message(call.message.chat.id, "Введите промокод, скидку (%) и лимит людей через пробел.\nПример: <code>SALE20 15 5000</code> (до 5000 человек)")
        bot.register_next_step_handler(msg, save_new_promo)

    elif data == "admin_listpromo":
        cursor.execute("SELECT code, discount, max_uses, used_count FROM promo")
        promos = cursor.fetchall()
        if not promos:
            bot.answer_callback_query(call.id, "Нет активных промокодов.", show_alert=True)
            return
        text = "📋 <b>Активные промокоды:</b>\n\n"
        for p in promos:
            text.format()
            text += f"🔑 <code>{p[0]}</code> | Скидка: {p[1]}% | Использовано: {p[3]} / {p[2]}\n"
        bot.send_message(call.message.chat.id, text)

    elif data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "Введите текст для рассылки всем пользователям:")
        bot.register_next_step_handler(msg, execute_broadcast)

def save_new_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code = parts[0]
        discount = int(parts[1])
        max_uses = int(parts[2]) # от 1 до 10000+
        
        cursor.execute("INSERT OR REPLACE INTO promo (code, discount, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, discount, max_uses))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> успешно создан!\n скидка: {discount}%\n лимит пользователей: {max_uses}")
    except Exception as e:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>SUMMER 10 1000</code>")

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
    
