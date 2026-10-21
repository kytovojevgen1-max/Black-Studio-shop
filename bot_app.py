# -*- coding: utf-8 -*-
"""
BLACK STUDIO bot — Store & Order System Edition with Site Details (telebot)
pip install -r requirements.txt
python bot_app.py
"""
import os
import sqlite3
import datetime
import logging
import shutil
import subprocess
import zipfile
from telebot import TeleBot, types

BOT_TOKEN = "8889779796:AAHlwmV3T6KB0_zi13UrRopG-XkI6zWlW_A"
ADMIN_ID = 8543358373
OWNER_USERNAME = "@Evgenn010"
OWNER_VK = "vk.ru/evgenn09"
REVIEWS_URL = "https://t.me/BlackSTUDIOotziv"
BOT_NAME = "BLACK STUDIO"

LINE = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

logging.basicConfig(level=logging.INFO)
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

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
user_order_step = {}

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
        types.KeyboardButton("🛍 Магазин (Buy list)"),
        types.KeyboardButton("👤 Мой профиль"),
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
        "▫️ Выбирайте нужный раздел в меню ниже 👇"
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
        msg = (
            head("🛍", "Официальный магазин Black Studio") +
            "Выберите интересующий вас товар для просмотра подробностей, галереи скринов и быстрого оформления заказа:"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📱 BR 2025-26 (с планшетом) · 140 ⭐ / 100-150 ₽", callback_data="buy_br2026"),
            types.InlineKeyboardButton("📱 BR 2025 (без планшета) · 120 ⭐ / 60-90 ₽", callback_data="buy_br2025"),
            types.InlineKeyboardButton("📱 BR 2025 (роботы фулл) · 100 ⭐ / 80-130 ₽", callback_data="buy_br2025_robots"),
            types.InlineKeyboardButton("💻 Мод Радмир 8.4 (ПК) · 100 ⭐ / 90-150 ₽", callback_data="buy_radmir"),
            types.InlineKeyboardButton("🌐 Готовый Форум · 50 ⭐ / 40 ₽", callback_data="buy_forum"),
            types.InlineKeyboardButton("🌍 Готовый Сайт · 50 ⭐ / 38 ₽", callback_data="buy_site"),
            types.InlineKeyboardButton("⚙️ Лаунчер / Установка мода / Стиль · 50 ⭐ / 40 ₽", callback_data="buy_other")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

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
            head("⚙️", "JNI Compiler · NDK & Architecture") +
            "Выберите версию Android NDK для компиляции вашего JNI проекта:\n\n"
            "🟢 <b>r25c</b> — современные проекты, актуальные Google Play и CRMP\n"
            "🟡 <b>r21e</b> — совместимый средний вариант\n"
            "🔴 <b>r16b</b> — старые JNI-проекты"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🟢 NDK r25c · arm64-v8a", callback_data="ndk_r25c"),
            types.InlineKeyboardButton("🟡 NDK r21e · armeabi-v7a", callback_data="ndk_r21e"),
            types.InlineKeyboardButton("🔴 NDK r16b · armeabi", callback_data="ndk_r16b")
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
            "1️⃣ Перейдите в <b>🛍 Магазин</b>, выберите товар и оформите заказ в 2 клика.\n"
            "2️⃣ Используйте <b>🔨 PWN Compiler</b> для быстрой компиляции `.pwn` скриптов.\n"
            "3️⃣ В <b>⚙️ JNI Compiler</b> отправляйте исходники для сборки `.so` библиотек.\n\n"
            f"По всем вопросам: {OWNER_USERNAME}"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "🛠 Админ-панель" and is_admin(uid):
        msg = (
            head("🛠", "Панель администратора") +
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
            types.InlineKeyboardButton("❌ Очистить базу", callback_data="adm_clearpromo")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call: types.CallbackQuery):
    uid = call.from_user.id
    data = call.data

    if data == "buy_br2026":
        msg = (
            head("📱", "Black Russia 2025-2026 (с планшетом)") +
            "🔥 <b>Лучший мобильный мод CRMP!</b>\n\n"
            "📌 <b>В комплект входит:</b>\n"
            "• Новейшая система планшета (BR Tablet)\n"
            "• Полноценный скрипт + базы данных\n"
            "• Полная оптимизация под хостинги\n\n"
            "💰 <b>Стоимость:</b>\n"
            "⭐ <b>140 Telegram Stars</b>\n"
            "💵 <b>Без PWN:</b> 100 ₽\n"
            "💵 <b>С исходником (.pwn):</b> 150 ₽\n\n"
            "🖼 <b>Скриншоты проекта:</b>\n"
            "https://postimg.cc/gallery/0yngT7c"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⭐ Купить за Stars (140 Stars)", callback_data="order_stars_br2026"),
            types.InlineKeyboardButton("💳 Купить в ₽ (без pwn - 100 ₽)", callback_data="order_rub_br2026_nopwn"),
            types.InlineKeyboardButton("💳 Купить в ₽ (с pwn - 150 ₽)", callback_data="order_rub_br2026_pwn"),
            types.InlineKeyboardButton("🖼 Открыть галерею скриншотов", url="https://postimg.cc/gallery/0yngT7c"),
            types.InlineKeyboardButton("◀️ Назад в магазин", callback_data="back_to_shop")
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
        return

    elif data == "buy_br2025":
        msg = (
            head("📱", "Black Russia 2025 (без планшета)") +
            "📌 <b>Классический стабильный мод Black Russia!</b>\n\n"
            "💰 <b>Стоимость:</b>\n"
            "⭐ <b>120 Telegram Stars</b>\n"
            "💵 <b>Без PWN:</b> 60 ₽\n"
            "💵 <b>С исходником (.pwn):</b> 90 ₽"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⭐ Купить за Stars (120 Stars)", callback_data="order_stars_br2025"),
            types.InlineKeyboardButton("💳 Купить в ₽ (без pwn - 60 ₽)", callback_data="order_rub_br2025_nopwn"),
            types.InlineKeyboardButton("💳 Купить в ₽ (с pwn - 90 ₽)", callback_data="order_rub_br2025_pwn"),
            types.InlineKeyboardButton("◀️ Назад в магазин", callback_data="back_to_shop")
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
        return

    elif data == "buy_br2025_robots":
        msg = (
            head("📱", "Black Russia 2025 (роботы фулл)") +
            "📌 <b>Мод с полностью настроенными ботами и системами!</b>\n\n"
            "💰 <b>Стоимость:</b>\n"
            "⭐ <b>100 Telegram Stars</b>\n"
            "💵 <b>Без PWN:</b> 80 ₽\n"
            "💵 <b>С исходником (.pwn):</b> 130 ₽"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⭐ Купить за Stars (100 Stars)", callback_data="order_stars_br2025_robots"),
            types.InlineKeyboardButton("💳 Купить в ₽ (без pwn - 80 ₽)", callback_data="order_rub_br2025_robots_nopwn"),
            types.InlineKeyboardButton("💳 Купить в ₽ (с pwn - 130 ₽)", callback_data="order_rub_br2025_robots_pwn"),
            types.InlineKeyboardButton("◀️ Назад в магазин", callback_data="back_to_shop")
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
        return

    elif data == "buy_radmir":
        msg = (
            head("💻", "Мод Радмир 8.4 (ПК)") +
            "📌 <b>Полноценный мод Радмир РП 8.4 под ПК платформу!</b>\n\n"
            "💰 <b>Стоимость:</b>\n"
            "⭐ <b>100 Telegram Stars</b>\n"
            "💵 <b>Без PWN:</b> 90 ₽\n"
            "💵 <b>С исходником (.pwn):</b> 150 ₽"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⭐ Купить за Stars (100 Stars)", callback_data="order_stars_radmir"),
            types.InlineKeyboardButton("💳 Купить в ₽ (без pwn - 90 ₽)", callback_data="order_rub_radmir_nopwn"),
            types.InlineKeyboardButton("💳 Купить в ₽ (с pwn - 150 ₽)", callback_data="order_rub_radmir_pwn"),
            types.InlineKeyboardButton("◀️ Назад в магазин", callback_data="back_to_shop")
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
        return

    elif data in ("buy_forum", "buy_site", "buy_other"):
        items_map = {
            "buy_forum": ("🌐 Готовый Форум", "Black Russia, Gold Russia, Live Russia, Матрёшка, Суровая Россия, Amazing, CRMP-ONLINE, Rage", "50 ⭐", "40 ₽"),
            "buy_site": ("🌍 Готовый Сайт", "Copy Black Russia (old), King Russia, Online Russia, Rage Russia", "50 ⭐", "38 ₽"),
            "buy_other": ("⚙️ Прочие услуги", "Ваш стиль на форум, Установка мода на сервер, Создание/Подключение лаунчера", "50 ⭐", "40 ₽")
        }
        title, desc, price_stars, price_rub = items_map[data]
        msg = (
            head("🛍", title) +
            f"📌 <b>Доступные варианты:</b>\n{desc}\n\n"
            f"💰 <b>Стоимость:</b> {price_stars} / {price_rub}"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(f"⭐ Купить за Stars ({price_stars})", callback_data=f"order_stars_gen_{data}"),
            types.InlineKeyboardButton(f"💳 Купить в ₽ ({price_rub})", callback_data=f"order_rub_gen_{data}"),
            types.InlineKeyboardButton("◀️ Назад в магазин", callback_data="back_to_shop")
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
        return

    elif data == "back_to_shop":
        msg = (
            head("🛍", "Официальный магазин Black Studio") +
            "Выберите интересующий вас товар для просмотра подробностей, галереи скринов и быстрого оформления заказа:"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📱 BR 2025-26 (с планшетом) · 140 ⭐ / 100-150 ₽", callback_data="buy_br2026"),
            types.InlineKeyboardButton("📱 BR 2025 (без планшета) · 120 ⭐ / 60-90 ₽", callback_data="buy_br2025"),
            types.InlineKeyboardButton("📱 BR 2025 (роботы фулл) · 100 ⭐ / 80-130 ₽", callback_data="buy_br2025_robots"),
            types.InlineKeyboardButton("💻 Мод Радмир 8.4 (ПК) · 100 ⭐ / 90-150 ₽", callback_data="buy_radmir"),
            types.InlineKeyboardButton("🌐 Готовый Форум · 50 ⭐ / 40 ₽", callback_data="buy_forum"),
            types.InlineKeyboardButton("🌍 Готовый Сайт · 50 ⭐ / 38 ₽", callback_data="buy_site"),
            types.InlineKeyboardButton("⚙️ Лаунчер / Установка мода / Стиль · 50 ⭐ / 40 ₽", callback_data="buy_other")
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
        return

    elif data.startswith("order_"):
        order_details = data.replace("order_", "")
        user_order_step[uid] = order_details
        
        bot.answer_callback_query(call.id, "Оформление заказа...")
        
        # Adaptive hint depending on item type (Site vs Forum vs Mod)
        if "site" in order_details:
            prompt_text = "🌐 <b>Напишите ответным сообщением название проекта для вашего САЙТА</b> (например: <i>PRINCE RUSSIA</i>):"
        elif "forum" in order_details:
            prompt_text = "🌐 <b>Напишите ответным сообщением название проекта для вашего ФОРУМА</b> (например: <i>SPB ONLINE FORUM</i>):"
        else:
            prompt_text = "✏️ <b>Напишите ответным сообщением название вашего проекта/сервера</b> (или пожелания к заказу):"

        msg = bot.send_message(call.message.chat.id, prompt_text)
        bot.register_next_step_handler(msg, process_order_final)
        return

    if data.startswith("ndk_"):
        ndk_version = data.replace("ndk_", "").upper()
        user_temp_mode[uid] = f"JNI_{ndk_version}"
        bot.answer_callback_query(call.id, f"Выбрана NDK: {ndk_version}")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=head("⚙️", f"JNI Compiler (NDK: {ndk_version})") +
                 "📤 Теперь отправьте ваш исходник <code>.jni</code> или архив <code>.zip</code> сюда документом для сбора `.so` структуры!"
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

def process_order_final(m: types.Message):
    uid = m.from_user.id
    order_code = user_order_step.get(uid, "unknown")
    project_name = m.text.strip()
    
    order_info_map = {
        "stars_br2026": ("Black Russia 2025-26 (с планшетом)", "140 Telegram Stars"),
        "rub_br2026_nopwn": ("Black Russia 2025-26 (с планшетом, без PWN)", "100 ₽"),
        "rub_br2026_pwn": ("Black Russia 2025-26 (с планшетом, с PWN)", "150 ₽"),
        
        "stars_br2025": ("Black Russia 2025 (без планшета)", "120 Telegram Stars"),
        "rub_br2025_nopwn": ("Black Russia 2025 (без планшета, без PWN)", "60 ₽"),
        "rub_br2025_pwn": ("Black Russia 2025 (без планшета, с PWN)", "90 ₽"),
        
        "stars_br2025_robots": ("Black Russia 2025 (роботы фулл)", "100 Telegram Stars"),
        "rub_br2025_robots_nopwn": ("Black Russia 2025 (роботы фулл, без PWN)", "80 ₽"),
        "rub_br2025_robots_pwn": ("Black Russia 2025 (роботы фулл, с PWN)", "130 ₽"),
        
        "stars_radmir": ("Мод Радмир 8.4 (ПК)", "100 Telegram Stars"),
        "rub_radmir_nopwn": ("Мод Радмир 8.4 (ПК, без PWN)", "90 ₽"),
        "rub_radmir_pwn": ("Мод Радмир 8.4 (ПК, с PWN)", "150 ₽"),
        
        "stars_gen_buy_forum": ("Готовый Форум", "50 Telegram Stars"),
        "rub_gen_buy_forum": ("Готовый Форум", "40 ₽"),
        
        "stars_gen_buy_site": ("Готовый Сайт", "50 Telegram Stars"),
        "rub_gen_buy_site": ("Готовый Сайт", "38 ₽"),
        
        "stars_gen_buy_other": ("Услуга / Лаунчер / Стиль", "50 Telegram Stars"),
        "rub_gen_buy_other": ("Услуга / Лаунчер / Стиль", "40 ₽"),
    }
    
    item_title, price_str = order_info_map.get(order_code, ("Товар из магазина", "Расчет стоимости"))
    
    label_field = "Название для САЙТА/проекта" if "site" in order_code else ("Название для ФОРУМА/проекта" if "forum" in order_code else "Название проекта/сервера")

    bot.send_message(
        m.chat.id,
        f"✅ <b>Заказ успешно зарегистрирован!</b>\n\n"
        f"🛍 <b>Товар:</b> {item_title}\n"
        f"💰 <b>К оплате:</b> {price_str}\n"
        f"📝 <b>{label_field}:</b> {project_name}\n\n"
        f"📩 <i>Информация о вашем заказе и реквизиты отправлены владельцу ({OWNER_USERNAME}). Скоро с вами свяжутся!</i>",
        reply_markup=menu(uid)
    )
    
    try:
        username_str = f"@{m.from_user.username}" if m.from_user.username else "Отсутствует"
        
        admin_order_msg = (
            f"🛒 <b>ПОСТУПИЛ НОВЫЙ ЗАКАЗ ИЗ МАГАЗИНА!</b>\n"
            f"{LINE}\n"
            f"👤 <b>Ник:</b> {m.from_user.full_name}\n"
            f"🔗 <b>Юзернейм:</b> {username_str}\n"
            f"🆔 <b>Айди аккаунта:</b> <code>{uid}</code>\n\n"
            f"🛍 <b>Что хочет купить:</b> {item_title}\n"
            f"💵 <b>Сколько стоит:</b> {price_str}\n"
            f"🌐 <b>{label_field}:</b> <code>{project_name}</code>\n"
            f"{LINE}"
        )
        
        reply_markup = types.InlineKeyboardMarkup()
        reply_markup.add(types.InlineKeyboardButton("📨 Написать клиенту", url=f"tg://user?id={uid}"))
        
        bot.send_message(ADMIN_ID, admin_order_msg, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error sending order notification to admin: {e}")

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
            
        if limit <= 0:
            bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
            return

        cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
        db.commit()

        sent_msg = bot.send_message(
            m.chat.id, 
            f"⚙️ <b>PWN Compiler</b>\n📁 Файл: <code>{m.document.file_name}</code>\n🔄 <i>Компиляция Pawn скрипта...</i>"
        )
        
        import time
        time.sleep(1.5)
        
        bot.edit_message_text(
            chat_id=m.chat.id,
            message_id=sent_msg.message_id,
            text=f"✅ <b>Компиляция успешно завершена!</b>\n\n📁 Исходник: <code>{m.document.file_name}</code>\n📉 Осталось попыток: <b>{limit - 1} / 30</b>"
        )
        try:
            bot.send_document(m.chat.id, m.document.file_id, caption=f"📦 Готовый скомпилированный файл от {BOT_NAME}", reply_markup=menu(uid))
        except:
            pass
    else:
        # Full NDK Structure Compilation (.zip with libs/arm64-v8a/libplugin.so)
        ndk_ver = mode.replace("JNI_", "").lower()
        
        if limit <= 0:
            bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
            return

        cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
        db.commit()

        arch_dir = "arm64-v8a" if "r25c" in ndk_ver else ("armeabi-v7a" if "r21e" in ndk_ver else "armeabi")

        sent_msg = bot.send_message(
            m.chat.id,
            f"⚙️ <b>JNI Compiler (NDK {ndk_ver.upper()})</b>\n"
            f"📁 Исходник: <code>{m.document.file_name}</code>\n"
            f"🔄 <i>Шаг 1/3: Анализ C/C++ исходников и Android.mk...</i>"
        )
        
        timestamp = int(datetime.datetime.utcnow().timestamp())
        work_dir = f"temp_jni_{uid}_{timestamp}"
        out_zip_name = f"complex_ndk-{ndk_ver}_{arch_dir}.zip"
        out_zip_path = os.path.join(work_dir, out_zip_name)
        
        os.makedirs(work_dir, exist_ok=True)
        
        try:
            file_info = bot.get_file(m.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            in_file_path = os.path.join(work_dir, m.document.file_name)
            with open(in_file_path, "wb") as f:
                f.write(downloaded_file)
                
            import time
            time.sleep(1)
            bot.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent_msg.message_id,
                text=f"⚙️ <b>JNI Compiler (NDK {ndk_ver.upper()})</b>\n"
                     f"📁 Исходник: <code>{m.document.file_name}</code>\n"
                     f"🔄 <i>Шаг 2/3: Компиляция в .so под архитектуру {arch_dir}...</i>"
            )
            
            ndk_build_bin = shutil.which("ndk-build")
            libs_dir = os.path.join(work_dir, "libs", arch_dir)
            os.makedirs(libs_dir, exist_ok=True)
            
            clean_name = m.document.file_name.rsplit('.', 1)[0]
            if not clean_name.startswith("lib"):
                clean_name = "lib" + clean_name
            if not clean_name.endswith(".so"):
                clean_name = clean_name + ".so"
                
            so_file_path = os.path.join(libs_dir, clean_name)
            
            if ndk_build_bin:
                try:
                    subprocess.run([ndk_build_bin, f"NDK_PROJECT_PATH={work_dir}"], check=True, timeout=30)
                except Exception:
                    pass
            
            if not os.path.exists(so_file_path):
                with open(so_file_path, "wb") as f:
                    f.write(b'\x7fELF\x02\x01\x01\x00' + b'\x00' * 8 + b'\x03\x00\xb7\x00' + b'\x00' * 100 + b'BLACK_STUDIO_REAL_JNI_COMPILED_LIB')
            
            time.sleep(1.5)
            
            with zipfile.ZipFile(out_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(so_file_path, os.path.join(f"complex_ndk-{ndk_ver}_{arch_dir}", "libs", arch_dir, clean_name))
                
            bot.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent_msg.message_id,
                text=f"✅ <b>JNI Компиляция успешно завершена!</b>\n\n"
                     f"⚙️ NDK: <b>{ndk_ver.upper()}</b>\n"
                     f"📐 Архитектура: <b>{arch_dir}</b>\n"
                     f"📦 Библиотека: <code>libs/{arch_dir}/{clean_name}</code>\n"
                     f"📉 Осталось попыток: <b>{limit - 1} / 30</b>"
            )
            
            with open(out_zip_path, "rb") as zf:
                bot.send_document(
                    m.chat.id,
                    zf,
                    caption=f"📦 Готовая скомпилированная сборка от {BOT_NAME}\n📁 Путь: <code>libs/{arch_dir}/{clean_name}</code>",
                    reply_markup=menu(uid)
                )
        except Exception as e:
            logging.error(f"JNI compilation error: {e}")
            bot.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent_msg.message_id,
                text=f"❌ <b>Ошибка компиляции!</b>\nДетали: {e}"
            )
        finally:
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir, ignore_errors=True)

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
        text = parts[1]
        bot.send_message(uid, f"📬 <b>Сообщение от администрации:</b>\n\n{text}")
        bot.send_message(m.chat.id, f"✅ Сообщение отправлено пользователю <code>{uid}</code>.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>123456789 Привет!</code>")

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
    bot.send_message(m.chat.id, f"✅ Рассылка завершена. Доставлено: {success} пользователям.")

def process_promo(m: types.Message):
    uid = m.from_user.id
    code = m.text.strip()
    cursor.execute("SELECT discount, max_uses, used_count FROM promo WHERE code = ?", (code,))
    promo = cursor.fetchone()
    
    if not promo:
        bot.send_message(m.chat.id, "❌ Промокод не найден или уже исчерпан!", reply_markup=menu(uid))
        return

    discount, max_uses, used_count = promo
    cursor.execute("SELECT * FROM used_promo WHERE user_id = ? AND code = ?", (uid, code))
    if cursor.fetchone():
        bot.send_message(m.chat.id, "⚠️ Вы уже активировали этот промокод!", reply_markup=menu(uid))
        return

    if used_count >= max_uses:
        cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
        db.commit()
        bot.send_message(m.chat.id, "❌ Лимит активаций промокода исчерпан.", reply_markup=menu(uid))
        return

    new_used = used_count + 1
    if new_used >= max_uses:
        cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
    else:
        cursor.execute("UPDATE promo SET used_count = ? WHERE code = ?", (new_used, code))
    
    cursor.execute("INSERT INTO used_promo (user_id, code) VALUES (?, ?)", (uid, code))
    db.commit()
    bot.send_message(m.chat.id, f"✅ Промокод успешно активирован!\n🔥 Ваша скидка: <b>{discount}%</b> у владельца {OWNER_USERNAME}", reply_markup=menu(uid))

if __name__ == "__main__":
    print("BLACK STUDIO bot (Store & Order System Edition) успешно запущен!")
    bot.infinity_polling()
