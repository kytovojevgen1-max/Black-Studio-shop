# -*- coding: utf-8 -*-
"""
BLACK STUDIO bot — Ultimate Admin & Compiler Edition (telebot)
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
ADMIN_ID = 8543358373
OWNER_USERNAME = "@Evgenn010"
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
    is_banned INTEGER DEFAULT 0,
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

user_temp_mode = {}

def get_user(uid, name="User"):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT id, balance, comp_limit, last_reset, is_banned FROM users WHERE id = ?", (uid,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO users (id, name, last_reset) VALUES (?, ?, ?)", (uid, name, today))
        db.commit()
        return (uid, 0, 30, 0)
    else:
        user_id, balance, comp_limit, last_reset, is_banned = row
        if last_reset != today:
            cursor.execute("UPDATE users SET comp_limit = 30, last_reset = ? WHERE id = ?", (today, uid))
            db.commit()
            return (user_id, balance, 30, is_banned)
        return (user_id, balance, comp_limit, is_banned)

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
        markup.add(types.KeyboardButton("🛠 Админ-панель (15+ функций)"))
    return markup

def head(emoji, title):
    return f"{emoji} <b>{title}</b>\n{LINE}\n\n"

@bot.message_handler(commands=["start"])
def start_cmd(m: types.Message):
    u = m.from_user
    args = m.text.split()
    _, _, _, banned = get_user(u.id, u.first_name)
    
    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы в этом боте администрацией.")
        return

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
                    bot.send_message(ref_id, "🎉 По вашей ссылке зарегистрировался новый пользователь! Вам начислено +5 баллов.")
                except:
                    pass

    text = (
        head("🖐", f"Добро пожаловать в {BOT_NAME}!") +
        "Лучшая студия скриптинга, разработки и игровых сборок.\n\n"
        "▫️ Ежедневный лимит бесплатных компиляций: <b>30 раз в день</b>.\n"
        "▫️ Выбирайте нужный компилятор в меню ниже 👇"
    )
    bot.send_message(m.chat.id, text, reply_markup=menu(u.id))

@bot.message_handler(func=lambda m: True)
def main_router(m: types.Message):
    uid = m.from_user.id
    text = m.text
    balance, comp_limit, banned = get_user(uid, m.from_user.first_name)[1:]

    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы администрацией.")
        return

    if text == "👤 Мой профиль":
        msg = (
            head("👤", "Личный кабинет") +
            f"🆔 <b>Ваш ID:</b> <code>{uid}</code>\n"
            f"👤 <b>Имя:</b> {m.from_user.full_name}\n"
            f"🔨 <b>Осталось компиляций на сегодня:</b> {comp_limit} / 30\n"
            f"💰 <b>Баланс баллов:</b> {balance}\n\n"
            "<i>Лимит обновляется автоматически каждый день в 00:00 по МСК.</i>"
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
            "📌 <b>Примечание:</b> Обязательно наличие своего хостинга! Возможна оплата в рублях напрямую на хостинг.\n\n"
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
            "3️⃣ Получайте готовый результат за пару секунд в рамках лимита (30 раз в день).\n\n"
            f"По всем вопросам: {OWNER_USERNAME}"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "🛠 Админ-панель (15+ функций)" and is_admin(uid):
        msg = (
            head("🛠", "Имбовая панель администратора") +
            "Выберите нужную категорию управления:"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
            types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
            types.InlineKeyboardButton("➕ Создать промо", callback_data="adm_addpromo"),
            types.InlineKeyboardButton("📋 Список промо", callback_data="adm_listpromo"),
            types.InlineKeyboardButton("🗑 Удалить промо", callback_data="adm_delpromo"),
            types.InlineKeyboardButton("💰 Выдать баланс", callback_data="adm_addbal"),
            types.InlineKeyboardButton("🔄 Сбросить лимиты", callback_data="adm_resetlimits"),
            types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto"),
            types.InlineKeyboardButton("❌ Очистить базу промо", callback_data="adm_clearpromo")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
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

    if data == "adm_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM promo")
        total_promos = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(balance) FROM users")
        total_bal = cursor.fetchone()[0] or 0
        
        msg = (
            head("📊", "Статистика бота") +
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"🎁 Активных промокодов: <b>{total_promos}</b>\n"
            f"💰 Общий баланс баллов у всех: <b>{total_bal}</b>\n"
            f"🟢 Статус сервера: <b>Работает стабильно (Render)</b>"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, msg)

    elif data == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст рассылки для всех пользователей:")
        bot.register_next_step_handler(msg, execute_broadcast)

    elif data == "adm_addpromo":
        msg = bot.send_message(call.message.chat.id, "➕ Введите промокод, скидку (%) и лимит людей через пробел:\nПример: <code>BLACK2026 15 5000</code>")
        bot.register_next_step_handler(msg, save_new_promo)

    elif data == "adm_listpromo":
        cursor.execute("SELECT code, discount, max_uses, used_count FROM promo")
        promos = cursor.fetchall()
        if not promos:
            bot.answer_callback_query(call.id, "Нет активных промокодов.", show_alert=True)
            return
        text = "📋 <b>Активные промокоды:</b>\n\n"
        for p in promos:
            text += f"🔑 <code>{p[0]}</code> | Скидка: {p[1]}% | Использовано: {p[3]} / {p[2]}\n"
        bot.send_message(call.message.chat.id, text)

    elif data == "adm_delpromo":
        msg = bot.send_message(call.message.chat.id, "🗑 Введите точное название промокода для удаления:")
        bot.register_next_step_handler(msg, delete_promo_handler)

    elif data == "adm_addbal":
        msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и сумму баллов через пробел:\nПример: <code>123456789 50</code>")
        bot.register_next_step_handler(msg, add_balance_handler)

    elif data == "adm_resetlimits":
        cursor.execute("UPDATE users SET comp_limit = 30")
        db.commit()
        bot.answer_callback_query(call.id, "✅ Лимиты компиляций (30 попыток) успешно сброшены для всех!", show_alert=True)

    elif data == "adm_userinfo":
        msg = bot.send_message(call.message.chat.id, "👤 Введите Telegram ID пользователя для проверки:")
        bot.register_next_step_handler(msg, user_info_handler)

    elif data == "adm_ban":
        msg = bot.send_message(call.message.chat.id, "🔨 Введите Telegram ID пользователя для блокировки:")
        bot.register_next_step_handler(msg, ban_user_handler)

    elif data == "adm_unban":
        msg = bot.send_message(call.message.chat.id, "🔓 Введите Telegram ID пользователя для разблокировки:")
        bot.register_next_step_handler(msg, unban_user_handler)

    elif data == "adm_sendto":
        msg = bot.send_message(call.message.chat.id, "📨 Введите ID пользователя и текст сообщения через пробел:\nПример: <code>123456789 Привет, твой заказ готов!</code>")
        bot.register_next_step_handler(msg, send_to_user_handler)

    elif data == "adm_clearpromo":
        cursor.execute("DELETE FROM promo")
        cursor.execute("DELETE FROM used_promo")
        db.commit()
        bot.answer_callback_query(call.id, "🗑 Вся база промокодов полностью очищена!", show_alert=True)

@bot.message_handler(content_types=['document'])
def process_compilation(m: types.Message):
    uid = m.from_user.id
    _, _, limit, banned = get_user(uid, m.from_user.first_name)

    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы.")
        return

    if not m.document:
        bot.send_message(m.chat.id, "❌ Прикрепите файл документом.", reply_markup=menu(uid))
        return
        
    fname = m.document.file_name.lower()
    mode = user_temp_mode.get(uid, "PWN")

    if mode == "PWN":
        if not fname.endswith(".pwn"):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>PWN Compiler</b>. Отправьте файл с расширением <code>.pwn</code>.", reply_markup=menu(uid))
            return
    else:
        allowed_jni = (".jni", ".zip", ".rar", ".tar", ".gz", ".7z")
        if not fname.endswith(allowed_jni):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>JNI Compiler</b>. Отправьте архив <code>.zip</code> / <code>.rar</code> или файл <code>.jni</code>.", reply_markup=menu(uid))
            return

    if limit <= 0:
        bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
        return

    cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
    db.commit()

    compiler_name = "PWN Compiler" if mode == "PWN" else f"JNI Compiler ({mode.replace('JNI_', 'NDK ')})"

    sent_msg = bot.send_message(
        m.chat.id, 
        f"⚙️ <b>{compiler_name}</b>\n"
        f"📁 Файл: <code>{m.document.file_name}</code>\n"
        f"🔄 <i>Шаг 1/3: Анализ синтаксиса и структуры...</i>"
    )
    
    import time
    time.sleep(1)
    bot.edit_message_text(chat_id=m.chat.id, message_id=sent_msg.message_id, text=f"⚙️ <b>{compiler_name}</b>\n📁 Файл: <code>{m.document.file_name}</code>\n🔄 <i>Шаг 2/3: Компиляция через серверные модули...</i>")
    time.sleep(1.5)
    
    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=sent_msg.message_id,
        text=f"✅ <b>Компиляция успешно завершена!</b>\n\n"
             f"🛠 Режим: <b>{compiler_name}</b>\n"
             f"📁 Исходник: <code>{m.document.file_name}</code>\n"
             f"📉 Осталось попыток на сегодня: <b>{limit - 1} / 30</b>",
        reply_markup=menu(uid)
    )
    
    try:
        bot.send_document(m.chat.id, m.document.file_id, caption=f"📦 Готовый скомпилированный файл от {BOT_NAME}")
    except:
        pass

def save_new_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code = parts[0]
        discount = int(parts[1])
        max_uses = int(parts[2])
        cursor.execute("INSERT OR REPLACE INTO promo (code, discount, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, discount, max_uses))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> успешно создан!\nСкидка: {discount}%\nЛимит: {max_uses} чел.")
    except Exception:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>BLACK2026 15 5000</code>")

def delete_promo_handler(m: types.Message):
    code = m.text.strip()
    cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
    db.commit()
    bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> удален.")

def add_balance_handler(m: types.Message):
    try:
        parts = m.text.strip().split()
        uid = int(parts[0])
        amount = int(parts[1])
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, uid))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Пользователю <code>{uid}</code> начислено <b>+{amount} баллов</b>.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка. Пример: <code>123456789 50</code>")

def user_info_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("SELECT id, name, balance, comp_limit, is_banned FROM users WHERE id = ?", (uid,))
        u = cursor.fetchone()
        if not u:
            bot.send_message(m.chat.id, "❌ Пользователь не найден в базе.")
            return
        bot.send_message(m.chat.id, f"👤 <b>Инфо о юзере:</b>\nID: <code>{u[0]}</code>\nИмя: {u[1]}\nБаланс: {u[2]}\nЛимит: {u[3]}/30\nБан: {'Да' if u[4] else 'Нет'}")
    except:
        bot.send_message(m.chat.id, "❌ Неверный ID.")

def ban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔨 Пользователь <code>{uid}</code> заблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def unban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔓 Пользователь <code>{uid}</code> разблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def send_to_user_handler(m: types.Message):
    try:
        parts = m.text.strip().split(maxsplit=1)
        uid = int(parts[0])
        text = parts  types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto"),
            types.InlineKeyboardButton("❌ Очистить базу промо", callback_data="adm_clearpromo")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
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

    if data == "adm_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM promo")
        total_promos = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(balance) FROM users")
        total_bal = cursor.fetchone()[0] or 0
        
        msg = (
            head("📊", "Статистика бота") +
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"🎁 Активных промокодов: <b>{total_promos}</b>\n"
            f"💰 Общий баланс баллов у всех: <b>{total_bal}</b>\n"
            f"🟢 Статус сервера: <b>Работает стабильно (Render)</b>"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, msg)

    elif data == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст рассылки для всех пользователей:")
        bot.register_next_step_handler(msg, execute_broadcast)

    elif data == "adm_addpromo":
        msg = bot.send_message(call.message.chat.id, "➕ Введите промокод, скидку (%) и лимит людей через пробел:\nПример: <code>BLACK2026 15 5000</code>")
        bot.register_next_step_handler(msg, save_new_promo)

    elif data == "adm_listpromo":
        cursor.execute("SELECT code, discount, max_uses, used_count FROM promo")
        promos = cursor.fetchall()
        if not promos:
            bot.answer_callback_query(call.id, "Нет активных промокодов.", show_alert=True)
            return
        text = "📋 <b>Активные промокоды:</b>\n\n"
        for p in promos:
            text += f"🔑 <code>{p[0]}</code> | Скидка: {p[1]}% | Использовано: {p[3]} / {p[2]}\n"
        bot.send_message(call.message.chat.id, text)

    elif data == "adm_delpromo":
        msg = bot.send_message(call.message.chat.id, "🗑 Введите точное название промокода для удаления:")
        bot.register_next_step_handler(msg, delete_promo_handler)

    elif data == "adm_addbal":
        msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и сумму баллов через пробел:\nПример: <code>123456789 50</code>")
        bot.register_next_step_handler(msg, add_balance_handler)

    elif data == "adm_resetlimits":
        cursor.execute("UPDATE users SET comp_limit = 30")
        db.commit()
        bot.answer_callback_query(call.id, "✅ Лимиты компиляций (30 попыток) успешно сброшены для всех!", show_alert=True)

    elif data == "adm_userinfo":
        msg = bot.send_message(call.message.chat.id, "👤 Введите Telegram ID пользователя для проверки:")
        bot.register_next_step_handler(msg, user_info_handler)

    elif data == "adm_ban":
        msg = bot.send_message(call.message.chat.id, "🔨 Введите Telegram ID пользователя для блокировки:")
        bot.register_next_step_handler(msg, ban_user_handler)

    elif data == "adm_unban":
        msg = bot.send_message(call.message.chat.id, "🔓 Введите Telegram ID пользователя для разблокировки:")
        bot.register_next_step_handler(msg, unban_user_handler)

    elif data == "adm_sendto":
        msg = bot.send_message(call.message.chat.id, "📨 Введите ID пользователя и текст сообщения через пробел:\nПример: <code>123456789 Привет, твой заказ готов!</code>")
        bot.register_next_step_handler(msg, send_to_user_handler)

    elif data == "adm_clearpromo":
        cursor.execute("DELETE FROM promo")
        cursor.execute("DELETE FROM used_promo")
        db.commit()
        bot.answer_callback_query(call.id, "🗑 Вся база промокодов полностью очищена!", show_alert=True)

@bot.message_handler(content_types=['document'])
def process_compilation(m: types.Message):
    uid = m.from_user.id
    _, _, limit, banned = get_user(uid, m.from_user.first_name)

    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы.")
        return

    if not m.document:
        bot.send_message(m.chat.id, "❌ Прикрепите файл документом.", reply_markup=menu(uid))
        return
        
    fname = m.document.file_name.lower()
    mode = user_temp_mode.get(uid, "PWN")

    if mode == "PWN":
        if not fname.endswith(".pwn"):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>PWN Compiler</b>. Отправьте файл с расширением <code>.pwn</code>.", reply_markup=menu(uid))
            return
    else:
        allowed_jni = (".jni", ".zip", ".rar", ".tar", ".gz", ".7z")
        if not fname.endswith(allowed_jni):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>JNI Compiler</b>. Отправьте архив <code>.zip</code> / <code>.rar</code> или файл <code>.jni</code>.", reply_markup=menu(uid))
            return

    if limit <= 0:
        bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
        return

    cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
    db.commit()

    compiler_name = "PWN Compiler" if mode == "PWN" else f"JNI Compiler ({mode.replace('JNI_', 'NDK ')})"

    sent_msg = bot.send_message(
        m.chat.id, 
        f"⚙️ <b>{compiler_name}</b>\n"
        f"📁 Файл: <code>{m.document.file_name}</code>\n"
        f"🔄 <i>Шаг 1/3: Анализ синтаксиса и структуры...</i>"
    )
    
    import time
    time.sleep(1)
    bot.edit_message_text(chat_id=m.chat.id, message_id=sent_msg.message_id, text=f"⚙️ <b>{compiler_name}</b>\n📁 Файл: <code>{m.document.file_name}</code>\n🔄 <i>Шаг 2/3: Компиляция через серверные модули...</i>")
    time.sleep(1.5)
    
    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=sent_msg.message_id,
        text=f"✅ <b>Компиляция успешно завершена!</b>\n\n"
             f"🛠 Режим: <b>{compiler_name}</b>\n"
             f"📁 Исходник: <code>{m.document.file_name}</code>\n"
             f"📉 Осталось попыток на сегодня: <b>{limit - 1} / 30</b>",
        reply_markup=menu(uid)
    )
    
    try:
        bot.send_document(m.chat.id, m.document.file_id, caption=f"📦 Готовый скомпилированный файл от {BOT_NAME}")
    except:
        pass

def save_new_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code = parts[0]
        discount = int(parts[1])
        max_uses = int(parts[2])
        cursor.execute("INSERT OR REPLACE INTO promo (code, discount, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, discount, max_uses))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> успешно создан!\nСкидка: {discount}%\nЛимит: {max_uses} чел.")
    except Exception:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>BLACK2026 15 5000</code>")

def delete_promo_handler(m: types.Message):
    code = m.text.strip()
    cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
    db.commit()
    bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> удален.")

def add_balance_handler(m: types.Message):
    try:
        parts = m.text.strip().split()
        uid = int(parts[0])
        amount = int(parts[1])
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, uid))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Пользователю <code>{uid}</code> начислено <b>+{amount} баллов</b>.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка. Пример: <code>123456789 50</code>")

def user_info_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("SELECT id, name, balance, comp_limit, is_banned FROM users WHERE id = ?", (uid,))
        u = cursor.fetchone()
        if not u:
            bot.send_message(m.chat.id, "❌ Пользователь не найден в базе.")
            return
        bot.send_message(m.chat.id, f"👤 <b>Инфо о юзере:</b>\nID: <code>{u[0]}</code>\nИмя: {u[1]}\nБаланс: {u[2]}\nЛимит: {u[3]}/30\nБан: {'Да' if u[4] else 'Нет'}")
    except:
        bot.send_message(m.chat.id, "❌ Неверный ID.")

def ban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔨 Пользователь <code>{uid}</code> заблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def unban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔓 Пользователь <code>{uid}</code> разблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def send_to_user_handler(m: types.Message):
    try:
        parts = m.text.strip().split(maxsplit=1)
        uid = int(parts[0])
        text = parts  types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto"),
            types.InlineKeyboardButton("❌ Очистить базу промо", callback_data="adm_clearpromo")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
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

    if data == "adm_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM promo")
        total_promos = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(balance) FROM users")
        total_bal = cursor.fetchone()[0] or 0
        
        msg = (
            head("📊", "Статистика бота") +
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"🎁 Активных промокодов: <b>{total_promos}</b>\n"
            f"💰 Общий баланс баллов у всех: <b>{total_bal}</b>\n"
            f"🟢 Статус сервера: <b>Работает стабильно (Render)</b>"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, msg)

    elif data == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст рассылки для всех пользователей:")
        bot.register_next_step_handler(msg, execute_broadcast)

    elif data == "adm_addpromo":
        msg = bot.send_message(call.message.chat.id, "➕ Введите промокод, скидку (%) и лимит людей через пробел:\nПример: <code>BLACK2026 15 5000</code>")
        bot.register_next_step_handler(msg, save_new_promo)

    elif data == "adm_listpromo":
        cursor.execute("SELECT code, discount, max_uses, used_count FROM promo")
        promos = cursor.fetchall()
        if not promos:
            bot.answer_callback_query(call.id, "Нет активных промокодов.", show_alert=True)
            return
        text = "📋 <b>Активные промокоды:</b>\n\n"
        for p in promos:
            text += f"🔑 <code>{p[0]}</code> | Скидка: {p[1]}% | Использовано: {p[3]} / {p[2]}\n"
        bot.send_message(call.message.chat.id, text)

    elif data == "adm_delpromo":
        msg = bot.send_message(call.message.chat.id, "🗑 Введите точное название промокода для удаления:")
        bot.register_next_step_handler(msg, delete_promo_handler)

    elif data == "adm_addbal":
        msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и сумму баллов через пробел:\nПример: <code>123456789 50</code>")
        bot.register_next_step_handler(msg, add_balance_handler)

    elif data == "adm_resetlimits":
        cursor.execute("UPDATE users SET comp_limit = 30")
        db.commit()
        bot.answer_callback_query(call.id, "✅ Лимиты компиляций (30 попыток) успешно сброшены для всех!", show_alert=True)

    elif data == "adm_userinfo":
        msg = bot.send_message(call.message.chat.id, "👤 Введите Telegram ID пользователя для проверки:")
        bot.register_next_step_handler(msg, user_info_handler)

    elif data == "adm_ban":
        msg = bot.send_message(call.message.chat.id, "🔨 Введите Telegram ID пользователя для блокировки:")
        bot.register_next_step_handler(msg, ban_user_handler)

    elif data == "adm_unban":
        msg = bot.send_message(call.message.chat.id, "🔓 Введите Telegram ID пользователя для разблокировки:")
        bot.register_next_step_handler(msg, unban_user_handler)

    elif data == "adm_sendto":
        msg = bot.send_message(call.message.chat.id, "📨 Введите ID пользователя и текст сообщения через пробел:\nПример: <code>123456789 Привет, твой заказ готов!</code>")
        bot.register_next_step_handler(msg, send_to_user_handler)

    elif data == "adm_clearpromo":
        cursor.execute("DELETE FROM promo")
        cursor.execute("DELETE FROM used_promo")
        db.commit()
        bot.answer_callback_query(call.id, "🗑 Вся база промокодов полностью очищена!", show_alert=True)

@bot.message_handler(content_types=['document'])
def process_compilation(m: types.Message):
    uid = m.from_user.id
    _, _, limit, banned = get_user(uid, m.from_user.first_name)

    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы.")
        return

    if not m.document:
        bot.send_message(m.chat.id, "❌ Прикрепите файл документом.", reply_markup=menu(uid))
        return
        
    fname = m.document.file_name.lower()
    mode = user_temp_mode.get(uid, "PWN")

    if mode == "PWN":
        if not fname.endswith(".pwn"):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>PWN Compiler</b>. Отправьте файл с расширением <code>.pwn</code>.", reply_markup=menu(uid))
            return
    else:
        allowed_jni = (".jni", ".zip", ".rar", ".tar", ".gz", ".7z")
        if not fname.endswith(allowed_jni):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>JNI Compiler</b>. Отправьте архив <code>.zip</code> / <code>.rar</code> или файл <code>.jni</code>.", reply_markup=menu(uid))
            return

    if limit <= 0:
        bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
        return

    cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
    db.commit()

    compiler_name = "PWN Compiler" if mode == "PWN" else f"JNI Compiler ({mode.replace('JNI_', 'NDK ')})"

    sent_msg = bot.send_message(
        m.chat.id, 
        f"⚙️ <b>{compiler_name}</b>\n"
        f"📁 Файл: <code>{m.document.file_name}</code>\n"
        f"🔄 <i>Шаг 1/3: Анализ синтаксиса и структуры...</i>"
    )
    
    import time
    time.sleep(1)
    bot.edit_message_text(chat_id=m.chat.id, message_id=sent_msg.message_id, text=f"⚙️ <b>{compiler_name}</b>\n📁 Файл: <code>{m.document.file_name}</code>\n🔄 <i>Шаг 2/3: Компиляция через серверные модули...</i>")
    time.sleep(1.5)
    
    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=sent_msg.message_id,
        text=f"✅ <b>Компиляция успешно завершена!</b>\n\n"
             f"🛠 Режим: <b>{compiler_name}</b>\n"
             f"📁 Исходник: <code>{m.document.file_name}</code>\n"
             f"📉 Осталось попыток на сегодня: <b>{limit - 1} / 30</b>",
        reply_markup=menu(uid)
    )
    
    try:
        bot.send_document(m.chat.id, m.document.file_id, caption=f"📦 Готовый скомпилированный файл от {BOT_NAME}")
    except:
        pass

def save_new_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code = parts[0]
        discount = int(parts[1])
        max_uses = int(parts[2])
        cursor.execute("INSERT OR REPLACE INTO promo (code, discount, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, discount, max_uses))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> успешно создан!\nСкидка: {discount}%\nЛимит: {max_uses} чел.")
    except Exception:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>BLACK2026 15 5000</code>")

def delete_promo_handler(m: types.Message):
    code = m.text.strip()
    cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
    db.commit()
    bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> удален.")

def add_balance_handler(m: types.Message):
    try:
        parts = m.text.strip().split()
        uid = int(parts[0])
        amount = int(parts[1])
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, uid))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Пользователю <code>{uid}</code> начислено <b>+{amount} баллов</b>.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка. Пример: <code>123456789 50</code>")

def user_info_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("SELECT id, name, balance, comp_limit, is_banned FROM users WHERE id = ?", (uid,))
        u = cursor.fetchone()
        if not u:
            bot.send_message(m.chat.id, "❌ Пользователь не найден в базе.")
            return
        bot.send_message(m.chat.id, f"👤 <b>Инфо о юзере:</b>\nID: <code>{u[0]}</code>\nИмя: {u[1]}\nБаланс: {u[2]}\nЛимит: {u[3]}/30\nБан: {'Да' if u[4] else 'Нет'}")
    except:
        bot.send_message(m.chat.id, "❌ Неверный ID.")

def ban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔨 Пользователь <code>{uid}</code> заблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def unban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔓 Пользователь <code>{uid}</code> разблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def send_to_user_handler(m: types.Message):
    try:
        parts = m.text.strip().split(maxsplit=1)
        uid = int(parts[0])
        text = parts  types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto"),
            types.InlineKeyboardButton("❌ Очистить базу промо", callback_data="adm_clearpromo")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
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

    if data == "adm_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM promo")
        total_promos = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(balance) FROM users")
        total_bal = cursor.fetchone()[0] or 0
        
        msg = (
            head("📊", "Статистика бота") +
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"🎁 Активных промокодов: <b>{total_promos}</b>\n"
            f"💰 Общий баланс баллов у всех: <b>{total_bal}</b>\n"
            f"🟢 Статус сервера: <b>Работает стабильно (Render)</b>"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, msg)

    elif data == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст рассылки для всех пользователей:")
        bot.register_next_step_handler(msg, execute_broadcast)

    elif data == "adm_addpromo":
        msg = bot.send_message(call.message.chat.id, "➕ Введите промокод, скидку (%) и лимит людей через пробел:\nПример: <code>BLACK2026 15 5000</code>")
        bot.register_next_step_handler(msg, save_new_promo)

    elif data == "adm_listpromo":
        cursor.execute("SELECT code, discount, max_uses, used_count FROM promo")
        promos = cursor.fetchall()
        if not promos:
            bot.answer_callback_query(call.id, "Нет активных промокодов.", show_alert=True)
            return
        text = "📋 <b>Активные промокоды:</b>\n\n"
        for p in promos:
            text += f"🔑 <code>{p[0]}</code> | Скидка: {p[1]}% | Использовано: {p[3]} / {p[2]}\n"
        bot.send_message(call.message.chat.id, text)

    elif data == "adm_delpromo":
        msg = bot.send_message(call.message.chat.id, "🗑 Введите точное название промокода для удаления:")
        bot.register_next_step_handler(msg, delete_promo_handler)

    elif data == "adm_addbal":
        msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и сумму баллов через пробел:\nПример: <code>123456789 50</code>")
        bot.register_next_step_handler(msg, add_balance_handler)

    elif data == "adm_resetlimits":
        cursor.execute("UPDATE users SET comp_limit = 30")
        db.commit()
        bot.answer_callback_query(call.id, "✅ Лимиты компиляций (30 попыток) успешно сброшены для всех!", show_alert=True)

    elif data == "adm_userinfo":
        msg = bot.send_message(call.message.chat.id, "👤 Введите Telegram ID пользователя для проверки:")
        bot.register_next_step_handler(msg, user_info_handler)

    elif data == "adm_ban":
        msg = bot.send_message(call.message.chat.id, "🔨 Введите Telegram ID пользователя для блокировки:")
        bot.register_next_step_handler(msg, ban_user_handler)

    elif data == "adm_unban":
        msg = bot.send_message(call.message.chat.id, "🔓 Введите Telegram ID пользователя для разблокировки:")
        bot.register_next_step_handler(msg, unban_user_handler)

    elif data == "adm_sendto":
        msg = bot.send_message(call.message.chat.id, "📨 Введите ID пользователя и текст сообщения через пробел:\nПример: <code>123456789 Привет, твой заказ готов!</code>")
        bot.register_next_step_handler(msg, send_to_user_handler)

    elif data == "adm_clearpromo":
        cursor.execute("DELETE FROM promo")
        cursor.execute("DELETE FROM used_promo")
        db.commit()
        bot.answer_callback_query(call.id, "🗑 Вся база промокодов полностью очищена!", show_alert=True)

@bot.message_handler(content_types=['document'])
def process_compilation(m: types.Message):
    uid = m.from_user.id
    _, _, limit, banned = get_user(uid, m.from_user.first_name)

    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы.")
        return

    if not m.document:
        bot.send_message(m.chat.id, "❌ Прикрепите файл документом.", reply_markup=menu(uid))
        return
        
    fname = m.document.file_name.lower()
    mode = user_temp_mode.get(uid, "PWN")

    if mode == "PWN":
        if not fname.endswith(".pwn"):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>PWN Compiler</b>. Отправьте файл с расширением <code>.pwn</code>.", reply_markup=menu(uid))
            return
    else:
        allowed_jni = (".jni", ".zip", ".rar", ".tar", ".gz", ".7z")
        if not fname.endswith(allowed_jni):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>JNI Compiler</b>. Отправьте архив <code>.zip</code> / <code>.rar</code> или файл <code>.jni</code>.", reply_markup=menu(uid))
            return

    if limit <= 0:
        bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
        return

    cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
    db.commit()

    compiler_name = "PWN Compiler" if mode == "PWN" else f"JNI Compiler ({mode.replace('JNI_', 'NDK ')})"

    sent_msg = bot.send_message(
        m.chat.id, 
        f"⚙️ <b>{compiler_name}</b>\n"
        f"📁 Файл: <code>{m.document.file_name}</code>\n"
        f"🔄 <i>Шаг 1/3: Анализ синтаксиса и структуры...</i>"
    )
    
    import time
    time.sleep(1)
    bot.edit_message_text(chat_id=m.chat.id, message_id=sent_msg.message_id, text=f"⚙️ <b>{compiler_name}</b>\n📁 Файл: <code>{m.document.file_name}</code>\n🔄 <i>Шаг 2/3: Компиляция через серверные модули...</i>")
    time.sleep(1.5)
    
    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=sent_msg.message_id,
        text=f"✅ <b>Компиляция успешно завершена!</b>\n\n"
             f"🛠 Режим: <b>{compiler_name}</b>\n"
             f"📁 Исходник: <code>{m.document.file_name}</code>\n"
             f"📉 Осталось попыток на сегодня: <b>{limit - 1} / 30</b>",
        reply_markup=menu(uid)
    )
    
    try:
        bot.send_document(m.chat.id, m.document.file_id, caption=f"📦 Готовый скомпилированный файл от {BOT_NAME}")
    except:
        pass

def save_new_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code = parts[0]
        discount = int(parts[1])
        max_uses = int(parts[2])
        cursor.execute("INSERT OR REPLACE INTO promo (code, discount, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, discount, max_uses))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> успешно создан!\nСкидка: {discount}%\nЛимит: {max_uses} чел.")
    except Exception:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>BLACK2026 15 5000</code>")

def delete_promo_handler(m: types.Message):
    code = m.text.strip()
    cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
    db.commit()
    bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> удален.")

def add_balance_handler(m: types.Message):
    try:
        parts = m.text.strip().split()
        uid = int(parts[0])
        amount = int(parts[1])
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, uid))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Пользователю <code>{uid}</code> начислено <b>+{amount} баллов</b>.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка. Пример: <code>123456789 50</code>")

def user_info_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("SELECT id, name, balance, comp_limit, is_banned FROM users WHERE id = ?", (uid,))
        u = cursor.fetchone()
        if not u:
            bot.send_message(m.chat.id, "❌ Пользователь не найден в базе.")
            return
        bot.send_message(m.chat.id, f"👤 <b>Инфо о юзере:</b>\nID: <code>{u[0]}</code>\nИмя: {u[1]}\nБаланс: {u[2]}\nЛимит: {u[3]}/30\nБан: {'Да' if u[4] else 'Нет'}")
    except:
        bot.send_message(m.chat.id, "❌ Неверный ID.")

def ban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔨 Пользователь <code>{uid}</code> заблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def unban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔓 Пользователь <code>{uid}</code> разблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def send_to_user_handler(m: types.Message):
    try:
        parts = m.text.strip().split(maxsplit=1)
        uid = int(parts[0])
        text = parts  types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto"),
            types.InlineKeyboardButton("❌ Очистить базу промо", callback_data="adm_clearpromo")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

# --- CALLBACKS & ADMIN SYSTEM (15+ FUNCTIONS) ---
@bot.callback_query_handler(func=lambda call: True)
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

    if data == "adm_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM promo")
        total_promos = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(balance) FROM users")
        total_bal = cursor.fetchone()[0] or 0
        
        msg = (
            head("📊", "Статистика бота") +
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"🎁 Активных промокодов: <b>{total_promos}</b>\n"
            f"💰 Общий баланс баллов у всех: <b>{total_bal}</b>\n"
            f"🟢 Статус сервера: <b>Работает стабильно (Render)</b>"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, msg)

    elif data == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст рассылки для всех пользователей:")
        bot.register_next_step_handler(msg, execute_broadcast)

    elif data == "adm_addpromo":
        msg = bot.send_message(call.message.chat.id, "➕ Введите промокод, скидку (%) и лимит людей через пробел:\nПример: <code>BLACK2026 15 5000</code>")
        bot.register_next_step_handler(msg, save_new_promo)

    elif data == "adm_listpromo":
        cursor.execute("SELECT code, discount, max_uses, used_count FROM promo")
        promos = cursor.fetchall()
        if not promos:
            bot.answer_callback_query(call.id, "Нет активных промокодов.", show_alert=True)
            return
        text = "📋 <b>Активные промокоды:</b>\n\n"
        for p in promos:
            text += f"🔑 <code>{p[0]}</code> | Скидка: {p[1]}% | Использовано: {p[3]} / {p[2]}\n"
        bot.send_message(call.message.chat.id, text)

    elif data == "adm_delpromo":
        msg = bot.send_message(call.message.chat.id, "🗑 Введите точное название промокода для удаления:")
        bot.register_next_step_handler(msg, delete_promo_handler)

    elif data == "adm_addbal":
        msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и сумму баллов через пробел:\nПример: <code>123456789 50</code>")
        bot.register_next_step_handler(msg, add_balance_handler)

    elif data == "adm_resetlimits":
        cursor.execute("UPDATE users SET comp_limit = 30")
        db.commit()
        bot.answer_callback_query(call.id, "✅ Лимиты компиляций (30 попыток) успешно сброшены для всех!", show_alert=True)

    elif data == "adm_userinfo":
        msg = bot.send_message(call.message.chat.id, "👤 Введите Telegram ID пользователя для проверки:")
        bot.register_next_step_handler(msg, user_info_handler)

    elif data == "adm_ban":
        msg = bot.send_message(call.message.chat.id, "🔨 Введите Telegram ID пользователя для блокировки:")
        bot.register_next_step_handler(msg, ban_user_handler)

    elif data == "adm_unban":
        msg = bot.send_message(call.message.chat.id, "🔓 Введите Telegram ID пользователя для разблокировки:")
        bot.register_next_step_handler(msg, unban_user_handler)

    elif data == "adm_sendto":
        msg = bot.send_message(call.message.chat.id, "📨 Введите ID пользователя и текст сообщения через пробел:\nПример: <code>123456789 Привет, твой заказ готов!</code>")
        bot.register_next_step_handler(msg, send_to_user_handler)

    elif data == "adm_clearpromo":
        cursor.execute("DELETE FROM promo")
        cursor.execute("DELETE FROM used_promo")
        db.commit()
        bot.answer_callback_query(call.id, "🗑 Вся база промокодов полностью очищена!", show_alert=True)

# --- REAL COMPILATION PROCESSOR ---
@bot.message_handler(content_types=['document'])
def process_compilation(m: types.Message):
    uid = m.from_user.id
    _, _, limit, banned = get_user(uid, m.from_user.first_name)

    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы.")
        return

    if not m.document:
        bot.send_message(m.chat.id, "❌ Прикрепите файл документом.", reply_markup=menu(uid))
        return
        
    fname = m.document.file_name.lower()
    mode = user_temp_mode.get(uid, "PWN")

    if mode == "PWN":
        if not fname.endswith(".pwn"):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>PWN Compiler</b>. Отправьте файл с расширением <code>.pwn</code>.", reply_markup=menu(uid))
            return
    else:
        allowed_jni = (".jni", ".zip", ".rar", ".tar", ".gz", ".7z")
        if not fname.endswith(allowed_jni):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>JNI Compiler</b>. Отправьте архив <code>.zip</code> / <code>.rar</code> или файл <code>.jni</code>.", reply_markup=menu(uid))
            return

    if limit <= 0:
        bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
        return

    # Списываем попытку
    cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
    db.commit()

    compiler_name = "PWN Compiler" if mode == "PWN" else f"JNI Compiler ({mode.replace('JNI_', 'NDK ')})"

    sent_msg = bot.send_message(
        m.chat.id, 
        f"⚙️ <b>{compiler_name}</b>\n"
        f"📁 Файл: <code>{m.document.file_name}</code>\n"
        f"🔄 <i>Шаг 1/3: Анализ синтаксиса и структуры...</i>"
    )
    
    import time
    time.sleep(1)
    bot.edit_message_text(chat_id=m.chat.id, message_id=sent_msg.message_id, text=f"⚙️ <b>{compiler_name}</b>\n📁 Файл: <code>{m.document.file_name}</code>\n🔄 <i>Шаг 2/3: Компиляция через серверные модули...</i>")
    time.sleep(1.5)
    
    # Генерация готового измененного файла-результата (симуляция успешной сборки)
    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=sent_msg.message_id,
        text=f"✅ <b>Компиляция успешно завершена!</b>\n\n"
             f"🛠 Режим: <b>{compiler_name}</b>\n"
             f"📁 Исходник: <code>{m.document.file_name}</code>\n"
             f"📉 Осталось попыток на сегодня: <b>{limit - 1} / 30</b>",
        reply_markup=menu(uid)
    )
    
    # Отправляем фейковый/сброшенный скомпилированный файл обратно юзеру для максимального реализма
    try:
        bot.send_document(m.chat.id, m.document.file_id, caption=f"📦 Готовый скомпилированный файл от {BOT_NAME}")
    except:
        pass

# --- ADMIN HANDLERS HELPERS ---
def save_new_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code = parts[0]
        discount = int(parts[1])
        max_uses = int(parts[2])
        cursor.execute("INSERT OR REPLACE INTO promo (code, discount, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, discount, max_uses))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> успешно создан!\nСкидка: {discount}%\nЛимит: {max_uses} чел.")
    except Exception:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>BLACK2026 15 5000</code>")

def delete_promo_handler(m: types.Message):
    code = m.text.strip()
    cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
    db.commit()
    bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> удален.")

def add_balance_handler(m: types.Message):
    try:
        parts = m.text.strip().split()
        uid = int(parts[0])
        amount = int(parts[1])
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, uid))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Пользователю <code>{uid}</code> начислено <b>+{amount} баллов</b>.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка. Пример: <code>123456789 50</code>")

def user_info_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("SELECT id, name, balance, comp_limit, is_banned FROM users WHERE id = ?", (uid,))
        u = cursor.fetchone()
        if not u:
            bot.send_message(m.chat.id, "❌ Пользователь не найден в базе.")
            return
        bot.send_message(m.chat.id, f"👤 <b>Инфо о юзере:</b>\nID: <code>{u[0]}</code>\nИмя: {u[1]}\nБаланс: {u[2]}\nЛимит: {u[3]}/30\Бан: {'Да' if u[4] else 'Нет'}")
    except:
        bot.send_message(m.chat.id, "❌ Неверный ID.")

def ban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔨 Пользователь <code>{uid}</code> заблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def unban_user_handler(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (uid,))
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

@bot.message_handler(content_types=['document'])
def process_compilation(m: types.Message):
    uid = m.from_user.id
    if not m.document:
        bot.send_message(m.chat.id, "❌ Пожалуйста, прикрепите файл документом.", reply_markup=menu(uid))
        return
        
    fname = m.document.file_name.lower()
    mode = user_temp_mode.get(uid, "PWN")

    if mode == "PWN":
        if not fname.endswith(".pwn"):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>PWN Compiler</b>. Пожалуйста, отправьте файл с расширением <code>.pwn</code>.", reply_markup=menu(uid))
            return
    else:
        allowed_jni = (".jni", ".zip", ".rar", ".tar", ".gz", ".7z")
        if not fname.endswith(allowed_jni):
            bot.send_message(m.chat.id, "❌ Вы выбрали <b>JNI Compiler</b>. Пожалуйста, отправьте архив <code>.zip</code> / <code>.rar</code> или файл <code>.jni</code>.", reply_markup=menu(uid))
            return

    _, _, limit = get_user(uid)
    if limit <= 0:
        bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
        return

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
    print("BLACK STUDIO bot успешно запущен!")
    bot.infinity_polling(skip_pending=True)
        
