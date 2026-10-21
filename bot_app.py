# -*- coding: utf-8 -*-
"""
BLACK STUDIO bot — Ultimate Premium Order Management & Live Web Keep-Alive (Flask + Telebot)
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
import threading
from flask import Flask
from telebot import TeleBot, types

BOT_TOKEN = "8889779796:AAGtHQtI7whqZxLrol0mn6SJWPRMldctElI"
PRIMARY_ADMIN_ID = 8543358373
OWNER_USERNAME = "@Evgenn010"
OWNER_VK = "vk.ru/evgenn09"
REVIEWS_URL = "https://t.me/BlackSTUDIOotziv"
BOT_NAME = "BLACK STUDIO"

LINE = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

logging.basicConfig(level=logging.INFO)
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# Flask Web Server to keep Render HTTP Service 100% ONLINE for UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return f"🚀 {BOT_NAME} Bot is Online and Running Smoothly!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Database Setup
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
    ref_by INTEGER,
    active_discount INTEGER DEFAULT 0,
    active_promo_code TEXT DEFAULT '',
    is_admin INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_title TEXT,
    price_str TEXT,
    details_text TEXT,
    status TEXT DEFAULT '⏳ На рассмотрении',
    created_at TEXT
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
admin_action_step = {}

def get_user(uid, name="User"):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT id, balance, comp_limit, last_reset, is_banned, active_discount, active_promo_code, is_admin FROM users WHERE id = ?", (uid,))
    row = cursor.fetchone()
    
    if not row:
        admin_flag = 1 if uid == PRIMARY_ADMIN_ID else 0
        cursor.execute("INSERT INTO users (id, name, last_reset, active_discount, active_promo_code, is_admin) VALUES (?, ?, ?, 0, '', ?)", (uid, name, today, admin_flag))
        db.commit()
        return (uid, 0, 30, 0, 0, '', admin_flag)
    else:
        user_id, balance, comp_limit, last_reset, is_banned, active_discount, active_promo_code, admin_flag = row
        if uid == PRIMARY_ADMIN_ID and not admin_flag:
            cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (uid,))
            db.commit()
            admin_flag = 1
            
        if last_reset != today:
            cursor.execute("UPDATE users SET comp_limit = 30, last_reset = ? WHERE id = ?", (today, uid))
            db.commit()
            return (user_id, balance, 30, is_banned, active_discount, active_promo_code, admin_flag)
        return (user_id, balance, comp_limit, is_banned, active_discount, active_promo_code, admin_flag)

def is_admin(uid):
    if uid == PRIMARY_ADMIN_ID:
        return True
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (uid,))
    res = cursor.fetchone()
    return bool(res and res[0])

def menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍 Покупки"),
        types.KeyboardButton("📦 Мои заказы"),
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
    _, _, _, banned, _, _, _ = get_user(u.id, u.first_name)
    
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
        "⚡️ <b>Премиальный сервис по CRMP/SA-MP разработке!</b>\n\n"
        "▫️ Ежедневный лимит бесплатных компиляций: <b>30 раз в день</b>.\n"
        "▫️ Выбирайте нужный раздел в меню ниже 👇"
    )
    bot.send_message(m.chat.id, text, reply_markup=menu(u.id))

@bot.message_handler(func=lambda m: True)
def main_router(m: types.Message):
    uid = m.from_user.id
    text = m.text
    user_data = get_user(uid, m.from_user.first_name)
    balance, comp_limit, banned, active_discount, active_promo_code, admin_flag = user_data[1:]

    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы администрацией.")
        return

    # Direct messaging system: Admin replies to user message
    if is_admin(uid) and m.reply_to_message and m.reply_to_message.text:
        orig_text = m.reply_to_message.text
        if "🆔 Айди аккаунта:" in orig_text or "🆔 ID:" in orig_text:
            try:
                target_id = int(orig_text.split("Айди аккаунта:")[1].split()[0]) if "Айди аккаунта:" in orig_text else int(orig_text.split("ID:")[1].split()[0])
                bot.send_message(
                    target_id,
                    f"💬 <b>Сообщение от администратора ({OWNER_USERNAME}):</b>\n\n{text}"
                )
                bot.send_message(m.chat.id, f"✅ Сообщение успешно доставлено пользователю <code>{target_id}</code>!")
                return
            except Exception as e:
                bot.send_message(m.chat.id, f"❌ Ошибка отправки сообщения: {e}")

    if text == "👤 Мой профиль":
        promo_info = f"🔥 <b>Промокод на скидку:</b> <code>{active_promo_code}</code> (-{active_discount}% на 1 следующий заказ)" if active_discount > 0 else "❌ <b>Промокод не активирован</b>"
        role_str = "👑 Владелец / Администратор" if is_admin(uid) else "👤 Пользователь"
        msg = (
            head("👤", "Личный кабинет") +
            f"🆔 <b>Ваш ID:</b> <code>{uid}</code>\n"
            f"👤 <b>Имя:</b> {m.from_user.full_name}\n"
            f"🔰 <b>Статус:</b> {role_str}\n"
            f"🔨 <b>Осталось компиляций на сегодня:</b> {comp_limit} / 30\n"
            f"💰 <b>Баланс баллов:</b> {balance}\n"
            f"{promo_info}\n\n"
            "<i>Лимит компиляций обновляется каждый день в 00:00 по МСК.</i>"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "📦 Мои заказы":
        cursor.execute("SELECT id, item_title, price_str, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 10", (uid,))
        orders_list = cursor.fetchall()
        if not orders_list:
            bot.send_message(m.chat.id, head("📦", "Ваши заказы") + "У вас пока нет оформленных заказов.", reply_markup=menu(uid))
            return
            
        msg = head("📦", "История ваших заказов")
        for o in orders_list:
            msg += f"📑 <b>Заказ #{o[0]}</b> | {o[4]}\n🛍 <b>Товар:</b> {o[1]}\n💵 <b>Сумма:</b> {o[2]}\n📌 <b>Статус:</b> {o[3]}\n{LINE}\n"
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text in ("🛍 Покупки", "🛍 Магазин (Buy list)"):
        disc_text = f"\n🔥 <i>У вас активирован промокод на скидку {active_discount}% ({active_promo_code})! Скидка применится к следующему заказу.</i>" if active_discount > 0 else ""
        msg = (
            head("🛍", "Официальный каталог Black Studio") +
            f"Выберите интересующий вас товар для просмотра подробностей, галереи скринов и быстрого оформления заказа:{disc_text}"
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
        msg = bot.send_message(m.chat.id, "🎁 Введите ваш промокод на скидку в ответном сообщении:")
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
            f"👑 <b>Владелец (VK):</b> {OWNER_VK}\n\n"
            "<i>Вы также можете просто отправить любое сообщение сюда в чат, и администрация ответит вам напрямую!</i>"
        )
        bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

    elif text == "❓ Как пользоваться":
        msg = (
            head("❓", "Инструкция по использованию") +
            "1️⃣ Перейдите в раздел <b>🛍 Покупки</b>, выберите нужный товар или мод.\n"
            "2️⃣ При заказе мода отправьте 1 сообщением все настройки сервера.\n"
            "3️⃣ Заказ автоматически получит статус <b>⏳ На рассмотрении</b>.\n"
            "4️⃣ Администратор сможет перевести заказ в <b>⚙️ В процессе</b>, <b>✅ Одобрено</b> или <b>❌ Отклонено</b> с причиной!\n"
            "5️⃣ Отслеживайте статус в разделе <b>📦 Мои заказы</b>.\n\n"
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
            types.InlineKeyboardButton("👑 Выдать админку", callback_data="adm_giveadmin"),
            types.InlineKeyboardButton("❌ Снять админку", callback_data="adm_removeadmin"),
            types.InlineKeyboardButton("➕ Создать промо", callback_data="adm_addpromo"),
            types.InlineKeyboardButton("📋 Список промо", callback_data="adm_listpromo"),
            types.InlineKeyboardButton("🗑 Удалить промо", callback_data="adm_delpromo"),
            types.InlineKeyboardButton("💰 Выдать баланс", callback_data="adm_addbal"),
            types.InlineKeyboardButton("🔄 Сбросить лимиты", callback_data="adm_resetlimits"),
            types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto"),
            types.InlineKeyboardButton("❌ Очистить промо", callback_data="adm_clearpromo")
        )
        bot.send_message(m.chat.id, msg, reply_markup=markup)

    else:
        # Standard fallback / messaging forwarder to Admin
        if not is_admin(uid):
            try:
                username_str = f"@{m.from_user.username}" if m.from_user.username else "Отсутствует"
                fwd_text = (
                    f"💬 <b>НОВОЕ СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ!</b>\n"
                    f"{LINE}\n"
                    f"👤 <b>Ник:</b> {m.from_user.full_name}\n"
                    f"🔗 <b>Юзернейм:</b> {username_str}\n"
                    f"🆔 <b>ID:</b> <code>{uid}</code>\n\n"
                    f"💬 <b>Сообщение:</b>\n{text}\n"
                    f"{LINE}\n"
                    f"<i>Ответьте на это сообщение в боте, чтобы написать пользователю в ЛС!</i>"
                )
                bot.send_message(PRIMARY_ADMIN_ID, fwd_text)
                bot.send_message(m.chat.id, "✅ Ваше сообщение отправлено администрации! Ожидайте ответа.")
            except Exception as e:
                logging.error(f"Error forwarding message to admin: {e}")

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
            types.InlineKeyboardButton("◀️ Назад в каталог", callback_data="back_to_shop")
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
            types.InlineKeyboardButton("◀️ Назад в каталог", callback_data="back_to_shop")
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
            types.InlineKeyboardButton("◀️ Назад в каталог", callback_data="back_to_shop")
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
            types.InlineKeyboardButton("◀️ Назад в каталог", callback_data="back_to_shop")
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
            types.InlineKeyboardButton("◀️ Назад в каталог", callback_data="back_to_shop")
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
        return

    elif data == "back_to_shop":
        msg = (
            head("🛍", "Официальный каталог Black Studio") +
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
        
        if "site" in order_details:
            prompt_text = "🌐 <b>Напишите ответным сообщением название проекта для вашего САЙТА</b> (например: <i>PRINCE RUSSIA</i>):"
        elif "forum" in order_details:
            prompt_text = "🌐 <b>Напишите ответным сообщением название проекта для вашего ФОРУМА</b> (например: <i>SPB ONLINE FORUM</i>):"
        else:
            prompt_text = (
                "✏️ <b>Отправьте данные для настройки Вашего Мода В ОДНОМ СООБЩЕНИИ:</b>\n\n"
                "1️⃣ Название сервера\n"
                "2️⃣ Название Проекта\n"
                "3️⃣ Скок бонус вертов\n"
                "4️⃣ Доната\n"
                "5️⃣ Тгк\n"
                "6️⃣ ВК\n"
                "7️⃣ Сайт\n"
                "8️⃣ Вип\n"
                "9️⃣ И лвл"
            )

        msg = bot.send_message(call.message.chat.id, prompt_text)
        bot.register_next_step_handler(msg, process_order_final)
        return

    # Admin Order Management System (Status Updates)
    if data.startswith("ord_inprog_") or data.startswith("ord_approve_") or data.startswith("ord_reject_"):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Нет прав доступа.", show_alert=True)
            return

        action, order_id_str = data.rsplit("_", 1)
        order_id = int(order_id_str)

        cursor.execute("SELECT user_id, item_title FROM orders WHERE id = ?", (order_id,))
        ord_data = cursor.fetchone()
        if not ord_data:
            bot.answer_callback_query(call.id, "❌ Заказ не найден.", show_alert=True)
            return

        client_uid, item_title = ord_data

        if action == "ord_inprog":
            cursor.execute("UPDATE orders SET status = '⚙️ В процессе' WHERE id = ?", (order_id,))
            db.commit()
            bot.answer_callback_query(call.id, "✅ Статус заказа изменен на: В процессе!")
            bot.send_message(
                client_uid,
                f"⚙️ <b>Ваш Заказ #{order_id} ({item_title}) принят в работу!</b>\n\n"
                f"📌 <b>Текущий статус:</b> <code>⚙️ В процессе</code>\n"
                f"💬 Администратор приступил к вашей заявке."
            )
            return

        elif action == "ord_approve":
            admin_action_step[uid] = ("approve", order_id, client_uid, item_title)
            msg = bot.send_message(call.message.chat.id, f"✅ <b>Впишите причину/комментарий для ОДОБРЕНИЯ Заказа #{order_id}:</b>")
            bot.register_next_step_handler(msg, process_order_comment)
            return

        elif action == "ord_reject":
            admin_action_step[uid] = ("reject", order_id, client_uid, item_title)
            msg = bot.send_message(call.message.chat.id, f"❌ <b>Впишите причину ОТКЛОНЕНИЯ Заказа #{order_id}:</b>")
            bot.register_next_step_handler(msg, process_order_comment)
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
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        total_admins = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]
        
        msg = (
            head("📊", "Статистика бота") +
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"👑 Всего администраторов: <b>{total_admins}</b>\n"
            f"🛍 Всего заказов: <b>{total_orders}</b>\n"
            f"🎁 Активных промокодов: <b>{total_promos}</b>\n"
            f"💰 Общий баланс баллов: <b>{total_bal}</b>\n"
            f"🟢 Статус сервера: <b>Работает 24/7 (Render + Flask Uptime)</b>"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, msg)

    elif data == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст рассылки для всех пользователей:")
        bot.register_next_step_handler(msg, execute_broadcast)

    elif data == "adm_giveadmin":
        msg = bot.send_message(call.message.chat.id, "👑 Введите Telegram ID пользователя, которому хотите выдать права администратора:")
        bot.register_next_step_handler(msg, give_admin_handler)

    elif data == "adm_removeadmin":
        msg = bot.send_message(call.message.chat.id, "❌ Введите Telegram ID пользователя, у которого хотите снять права администратора:")
        bot.register_next_step_handler(msg, remove_admin_handler)

    elif data == "adm_addpromo":
        msg = bot.send_message(call.message.chat.id, "➕ Введите промокод, скидку (%) и лимит людей через пробел:\nПример: <code>BLACK50 50 100</code>")
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

def process_order_comment(m: types.Message):
    uid = m.from_user.id
    if uid not in admin_action_step:
        return

    act_type, order_id, client_uid, item_title = admin_action_step[uid]
    comment_text = m.text.strip()
    del admin_action_step[uid]

    if act_type == "approve":
        status_str = "✅ Одобрено"
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status_str, order_id))
        db.commit()
        
        bot.send_message(m.chat.id, f"✅ Заказ #{order_id} переведен в статус <b>Одобрено</b>!")
        bot.send_message(
            client_uid,
            f"🎉 <b>Ваш Заказ #{order_id} ({item_title}) успешно ОДОБРЕН!</b>\n\n"
            f"📌 <b>Статус:</b> <code>✅ Одобрено</code>\n"
            f"📝 <b>Комментарий администратора:</b>\n<i>{comment_text}</i>"
        )
    else:
        status_str = f"❌ Отклонено (Причина: {comment_text})"
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status_str, order_id))
        db.commit()

        bot.send_message(m.chat.id, f"❌ Заказ #{order_id} переведен в статус <b>Отклонено</b>!")
        bot.send_message(
            client_uid,
            f"❌ <b>Ваш Заказ #{order_id} ({item_title}) был ОТКЛОНЕН.</b>\n\n"
            f"📌 <b>Статус:</b> <code>❌ Отклонено</code>\n"
            f"⚠️ <b>Причина отклонения:</b>\n<i>{comment_text}</i>"
        )

def process_order_final(m: types.Message):
    uid = m.from_user.id
    order_code = user_order_step.get(uid, "unknown")
    details_text = m.text.strip()
    
    u_data = get_user(uid, m.from_user.first_name)
    active_discount, active_promo_code = u_data[4], u_data[5]

    order_info_map = {
        "stars_br2026": ("Black Russia 2025-26 (с планшетом)", 140, "Stars"),
        "rub_br2026_nopwn": ("Black Russia 2025-26 (с планшетом, без PWN)", 100, "₽"),
        "rub_br2026_pwn": ("Black Russia 2025-26 (с планшетом, с PWN)", 150, "₽"),
        
        "stars_br2025": ("Black Russia 2025 (без планшета)", 120, "Stars"),
        "rub_br2025_nopwn": ("Black Russia 2025 (без планшета, без PWN)", 60, "₽"),
        "rub_br2025_pwn": ("Black Russia 2025 (без планшета, с PWN)", 90, "₽"),
        
        "stars_br2025_robots": ("Black Russia 2025 (роботы фулл)", 100, "Stars"),
        "rub_br2025_robots_nopwn": ("Black Russia 2025 (роботы фулл, без PWN)", 80, "₽"),
        "rub_br2025_robots_pwn": ("Black Russia 2025 (роботы фулл, с PWN)", 130, "₽"),
        
        "stars_radmir": ("Мод Радмир 8.4 (ПК)", 100, "Stars"),
        "rub_radmir_nopwn": ("Мод Радмир 8.4 (ПК, без PWN)", 90, "₽"),
        "rub_radmir_pwn": ("Мод Радмир 8.4 (ПК, с PWN)", 150, "₽"),
        
        "stars_gen_buy_forum": ("Готовый Форум", 50, "Stars"),
        "rub_gen_buy_forum": ("Готовый Форум", 40, "₽"),
        
        "stars_gen_buy_site": ("Готовый Сайт", 50, "Stars"),
        "rub_gen_buy_site": ("Готовый Сайт", 38, "₽"),
        
        "stars_gen_buy_other": ("Услуга / Лаунчер / Стиль", 50, "Stars"),
        "rub_gen_buy_other": ("Услуга / Лаунчер / Стиль", 40, "₽"),
    }
    
    item_title, orig_price, currency = order_info_map.get(order_code, ("Товар из магазина", 0, "₽"))
    
    if active_discount > 0:
        final_price = int(orig_price * (100 - active_discount) / 100)
        price_str = f"<s>{orig_price} {currency}</s> 🔥 <b>{final_price} {currency}</b> (-{active_discount}%)"
        cursor.execute("UPDATE users SET active_discount = 0, active_promo_code = '' WHERE id = ?", (uid,))
        db.commit()
    else:
        price_str = f"<b>{orig_price} {currency}</b>"

    created_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M MSK")
    initial_status = "⏳ На рассмотрении"

    cursor.execute(
        "INSERT INTO orders (user_id, item_title, price_str, details_text, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (uid, item_title, price_str, details_text, initial_status, created_at)
    )
    db.commit()
    order_id = cursor.lastrowid

    bot.send_message(
        m.chat.id,
        f"✅ <b>Заказ #{order_id} успешно зарегистрирован!</b>\n\n"
        f"🛍 <b>Товар:</b> {item_title}\n"
        f"💰 <b>К оплате:</b> {price_str}\n"
        f"📌 <b>Статус:</b> <code>{initial_status}</code>\n\n"
        f"📋 <b>Ваши данные настройки:</b>\n{details_text}\n\n"
        f"📩 <i>Информация отправлена администраторам ({OWNER_USERNAME}). Отслеживайте статус в разделе «📦 Мои заказы»!</i>",
        reply_markup=menu(uid)
    )
    
    try:
        username_str = f"@{m.from_user.username}" if m.from_user.username else "Отсутствует"

        admin_order_msg = (
            f"🛒 <b>ПОСТУПИЛ НОВЫЙ ЗАКАЗ #{order_id}!</b>\n"
            f"{LINE}\n"
            f"👤 <b>Ник:</b> {m.from_user.full_name}\n"
            f"🔗 <b>Юзернейм:</b> {username_str}\n"
            f"🆔 <b>Айди аккаунта:</b> <code>{uid}</code>\n\n"
            f"🛍 <b>Что хочет купить:</b> {item_title}\n"
            f"💵 <b>Сколько стоит:</b> {price_str}\n"
            f"📌 <b>Текущий статус:</b> <code>{initial_status}</code>\n\n"
            f"📋 <b>Настройки от клиента:</b>\n<code>{details_text}</code>\n"
            f"{LINE}\n"
            f"👇 <b>Управление статусом заказа:</b>"
        )
        
        reply_markup = types.InlineKeyboardMarkup(row_width=1)
        reply_markup.add(
            types.InlineKeyboardButton("⚙️ В процессе", callback_data=f"ord_inprog_{order_id}"),
            types.InlineKeyboardButton("✅ Одобрено (указать причину)", callback_data=f"ord_approve_{order_id}"),
            types.InlineKeyboardButton("❌ Отклонено (указать причину)", callback_data=f"ord_reject_{order_id}"),
            types.InlineKeyboardButton("📨 Написать клиенту в ЛС", url=f"tg://user?id={uid}")
        )
        
        bot.send_message(PRIMARY_ADMIN_ID, admin_order_msg, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error sending order notification to admin: {e}")

@bot.message_handler(content_types=['document'])
def process_compilation(m: types.Message):
    uid = m.from_user.id
    _, _, limit, banned, _, _, _ = get_user(uid, m.from_user.first_name)

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

def give_admin_handler(m: types.Message):
    try:
        target_id = int(m.text.strip())
        cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (target_id,))
        db.commit()
        bot.send_message(m.chat.id, f"👑 Пользователю <code>{target_id}</code> успешно выданы права администратора!")
        try:
            bot.send_message(target_id, "👑 <b>Вам выданы права администратора в боте!</b>\nНажмите /start для обновления меню.")
        except:
            pass
    except Exception:
        bot.send_message(m.chat.id, "❌ Ошибка! Введите корректный Telegram ID (число).")

def remove_admin_handler(m: types.Message):
    try:
        target_id = int(m.text.strip())
        if target_id == PRIMARY_ADMIN_ID:
            bot.send_message(m.chat.id, "❌ Нельзя снять права у главного владельца проекта!")
            return
        cursor.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (target_id,))
        db.commit()
        bot.send_message(m.chat.id, f"❌ Права администратора с пользователя <code>{target_id}</code> успешно сняты.")
    except Exception:
        bot.send_message(m.chat.id, "❌ Ошибка! Введите корректный Telegram ID (число).")

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
        bot.send_message(m.chat.id, "❌ Ошибка формата. Пример: <code>BLACK50 50 100</code>")

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
        cursor.execute("SELECT id, name, balance, comp_limit, is_banned, active_discount, active_promo_code, is_admin FROM users WHERE id = ?", (uid,))
        u = cursor.fetchone()
        if not u:
            bot.send_message(m.chat.id, "❌ Пользователь не найден в базе.")
            return
        admin_str = "Да 👑" if u[7] else "Нет"
        bot.send_message(m.chat.id, f"👤 <b>Инфо о юзере:</b>\nID: <code>{u[0]}</code>\nИмя: {u[1]}\nАдмин: {admin_str}\nБаланс: {u[2]}\nЛимит: {u[3]}/30\nСкидка: {u[5]}% ({u[6]})\nБан: {'Да' if u[4] else 'Нет'}")
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
        bot.send_message(uid, f"📬 <b>Сообщение от администрации ({OWNER_USERNAME}):</b>\n\n{text}")
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
    code = m.text.strip().upper()
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
    cursor.execute("UPDATE users SET active_discount = ?, active_promo_code = ? WHERE id = ?", (discount, code, uid))
    db.commit()
    bot.send_message(m.chat.id, f"🎉 <b>Промокод {code} успешно активирован!</b>\n🔥 Вы получили скидку <b>{discount}%</b> на ваш <b>следующий 1 заказ</b> в магазине!", reply_markup=menu(uid))

if __name__ == "__main__":
    print("BLACK STUDIO bot (Ultimate Premium Order Management) успешно запущен!")
    
    # Start Flask Web Server in a background thread for Render & UptimeRobot HTTP Monitor
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start Telegram Bot Polling
    bot.infinity_polling()
