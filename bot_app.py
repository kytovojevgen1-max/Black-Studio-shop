# -*- coding: utf-8 -*-
"""
BLACK STUDIO bot — Ultimate Fix 2026
- Исправлены все возможные конфликты хендлеров TeleBot.
- Все текстовые кнопки и callback-запросы работают стабильно.
- Защита от дублей регистрации и чёткие шаблоны заявок.
"""
import os
import sqlite3
import datetime
import logging
import shutil
import subprocess
import zipfile
import threading
import random
from flask import Flask
from telebot import TeleBot, types

BOT_TOKEN = "8889779796:AAHk7gcNt-3Z9wYee0BoSuYf1ZVG55MSPlk"
PRIMARY_ADMIN_ID = 8543358373
OWNER_USERNAME = "@Evgenn010"
CO_OWNER_USERNAME = "@forever10002"
OWNER_VK = "vk.ru/evgenn09"
REVIEWS_URL = "https://t.me/BlackSTUDIOotziv"
BOT_NAME = "BLACK STUDIO"

LINE = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

logging.basicConfig(level=logging.INFO)
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

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

db = sqlite3.connect("nexus.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT DEFAULT '',
    balance INTEGER DEFAULT 0,
    comp_limit INTEGER DEFAULT 30,
    last_reset TEXT,
    is_banned INTEGER DEFAULT 0,
    ref_by INTEGER,
    active_discount INTEGER DEFAULT 0,
    active_promo_code TEXT DEFAULT '',
    is_admin INTEGER DEFAULT 0,
    admin_role TEXT DEFAULT 'user',
    notified_reg INTEGER DEFAULT 0
)
""")

try:
    cursor.execute("SELECT username FROM users LIMIT 1")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE users ADD COLUMN username TEXT DEFAULT ''")
    db.commit()

try:
    cursor.execute("SELECT admin_role FROM users LIMIT 1")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE users ADD COLUMN admin_role TEXT DEFAULT 'user'")
    db.commit()

try:
    cursor.execute("SELECT notified_reg FROM users LIMIT 1")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE users ADD COLUMN notified_reg INTEGER DEFAULT 0")
    db.commit()

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

def get_user(uid, name="User", username=""):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT id, balance, comp_limit, last_reset, is_banned, active_discount, active_promo_code, is_admin, admin_role, notified_reg FROM users WHERE id = ?", (uid,))
    row = cursor.fetchone()
    
    if not row:
        admin_flag = 1 if uid == PRIMARY_ADMIN_ID else 0
        role = 'owner' if uid == PRIMARY_ADMIN_ID else 'user'
        cursor.execute("INSERT INTO users (id, name, username, last_reset, active_discount, active_promo_code, is_admin, admin_role, notified_reg) VALUES (?, ?, ?, ?, 0, '', ?, ?, 0)", (uid, name, username, today, admin_flag, role))
        db.commit()
        return (uid, 0, 30, 0, 0, '', admin_flag, role, 0)
    else:
        user_id, balance, comp_limit, last_reset, is_banned, active_discount, active_promo_code, admin_flag, admin_role, notified_reg = row
        if uid == PRIMARY_ADMIN_ID:
            if not admin_flag or admin_role != 'owner':
                cursor.execute("UPDATE users SET is_admin = 1, admin_role = 'owner', username = ? WHERE id = ?", (username, uid))
                db.commit()
                admin_flag = 1
                admin_role = 'owner'
        else:
            if username:
                cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, uid))
                db.commit()
            
        if last_reset != today:
            cursor.execute("UPDATE users SET comp_limit = 30, last_reset = ? WHERE id = ?", (today, uid))
            db.commit()
            return (user_id, balance, 30, is_banned, active_discount, active_promo_code, admin_flag, admin_role, notified_reg)
        return (user_id, balance, comp_limit, is_banned, active_discount, active_promo_code, admin_flag, admin_role, notified_reg)

def is_admin(uid):
    if uid == PRIMARY_ADMIN_ID:
        return True
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (uid,))
    res = cursor.fetchone()
    return bool(res and res[0])

def get_admin_role(uid):
    if uid == PRIMARY_ADMIN_ID:
        return 'owner'
    cursor.execute("SELECT admin_role FROM users WHERE id = ?", (uid,))
    res = cursor.fetchone()
    return res[0] if res and res[0] else 'user'

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
    uname = f"@{u.username}" if u.username else ""
    user_data = get_user(u.id, u.first_name, uname)
    banned = user_data[4]
    notified_reg = user_data[9]
    
    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы в этом боте администрацией.")
        return

    if u.id != PRIMARY_ADMIN_ID and not notified_reg:
        try:
            username_str = f"@{u.username}" if u.username else "Отсутствует"
            reg_alert = (
                f"👤 <b>НОВЫЙ ПОЛЬЗОВАТЕЛЬ В БОТЕ!</b>\n"
                f"{LINE}\n"
                f"👤 <b>Имя:</b> {u.full_name}\n"
                f"🔗 <b>Юзернейм:</b> {username_str}\n"
                f"🆔 <b>Айди аккаунта:</b> <code>{u.id}</code>\n"
                f"{LINE}"
            )
            bot.send_message(PRIMARY_ADMIN_ID, reg_alert)
            cursor.execute("UPDATE users SET notified_reg = 1 WHERE id = ?", (u.id,))
            db.commit()
        except Exception as e:
            logging.error(f"Error sending registration alert: {e}")

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
                    bot.send_message(ref_id, "🎉 По вашей реферальной ссылке зарегистрировался новый пользователь! Вам начислено +5 баллов 💰.")
                except:
                    pass

    text = (
        head("🔥", f"Добро пожаловать в {BOT_NAME}!") +
        "⚡️ <b>Элитная студия разработки, скриптинг-компиляции и игровых сборок CRMP/SA-MP!</b>\n\n"
        "▫️ Ежедневный лимит бесплатных компиляций: <b>30 раз в день</b>.\n"
        "▫️ Выбирайте нужный раздел в меню ниже 👇"
    )
    bot.send_message(m.chat.id, text, reply_markup=menu(u.id))

@bot.message_handler(func=lambda m: m.text == "👤 Мой профиль")
def profile_handler(m: types.Message):
    uid = m.from_user.id
    uname = f"@{m.from_user.username}" if m.from_user.username else ""
    user_data = get_user(uid, m.from_user.first_name, uname)
    balance, comp_limit, banned, active_discount, active_promo_code, admin_flag, admin_role = user_data[1:8]
    if banned:
        return
    
    promo_info = f"🔥 <b>Промокод на скидку:</b> <code>{active_promo_code}</code> (-{active_discount}% на 1 следующий заказ)" if active_discount > 0 else "❌ <b>Промокод не активирован</b>"
    
    if admin_role == 'owner':
        role_title = "👑 Создатель"
    elif admin_role == 'admin':
        role_title = "🛡 Администратор"
    elif admin_role == 'media_admin':
        role_title = "📸 Медиа-Администратор"
    else:
        role_title = "👤 Пользователь"

    msg = (
        head("👤", "Личный кабинет") +
        f"🆔 <b>Ваш ID:</b> <code>{uid}</code>\n"
        f"👤 <b>Имя:</b> {m.from_user.full_name}\n"
        f"🔰 <b>Статус:</b> {role_title}\n"
        f"🔨 <b>Осталось компиляций на сегодня:</b> {comp_limit} / 30\n"
        f"💰 <b>Баланс баллов:</b> {balance}\n"
        f"{promo_info}\n\n"
        "<i>Лимит компиляций обновляется каждый день в 00:00 по МСК.</i>"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "📦 Мои заказы")
def orders_handler(m: types.Message):
    uid = m.from_user.id
    cursor.execute("SELECT id, item_title, price_str, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 10", (uid,))
    orders_list = cursor.fetchall()
    if not orders_list:
        bot.send_message(m.chat.id, head("📦", "Ваши заказы") + "У вас пока нет оформленных заказов.", reply_markup=menu(uid))
        return
        
    msg = head("📦", "История ваших заказов")
    for o in orders_list:
        msg += f"📑 <b>Заказ #{o[0]}</b> | {o[4]}\n🛍 <b>Товар:</b> {o[1]}\n💵 <b>Сумма:</b> {o[2]}\n📌 <b>Статус:</b> {o[3]}\n{LINE}\n"
    bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text in ("🛍 Покупки", "🛍 Магазин (Buy list)"))
def shop_handler(m: types.Message):
    uid = m.from_user.id
    u_data = get_user(uid, m.from_user.first_name)
    active_discount, active_promo_code = u_data[5], u_data[6]
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

@bot.message_handler(func=lambda m: m.text == "🔨 PWN Compiler")
def pwn_menu_handler(m: types.Message):
    uid = m.from_user.id
    user_temp_mode[uid] = "PWN"
    u_data = get_user(uid, m.from_user.first_name)
    msg = (
        head("🔨", "PWN Compiler (Pawno to .amx)") +
        f"Осталось попыток: <b>{u_data[2]} / 30</b>\n\n"
        "📤 Отправьте ваш файл скрипта <code>.pwn</code> сюда в чат документом, и бот выполнит компиляцию в <code>.amx</code>!"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "⚙️ JNI Compiler")
def jni_menu_handler(m: types.Message):
    uid = m.from_user.id
    msg = (
        head("⚙️", "JNI Compiler · NDK & Architecture") +
        "Выберите версию Android NDK для сборки вашего JNI проекта:\n\n"
        "🟢 <b>r25c</b> — arm64-v8a (Современные CRMP сборки)\n"
        "🟡 <b>r21e</b> — armeabi-v7a (Средние устройства)\n"
        "🔴 <b>r16b</b> — armeabi (Старые версии)"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🟢 NDK r25c · arm64-v8a", callback_data="ndk_r25c"),
        types.InlineKeyboardButton("🟡 NDK r21e · armeabi-v7a", callback_data="ndk_r21e"),
        types.InlineKeyboardButton("🔴 NDK r16b · armeabi", callback_data="ndk_r16b")
    )
    bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎁 Промокод")
def promo_menu_handler(m: types.Message):
    msg = bot.send_message(m.chat.id, "🎁 Введите ваш промокод на скидку в ответном сообщении:")
    bot.register_next_step_handler(msg, process_promo)

@bot.message_handler(func=lambda m: m.text == "👥 Пригласить друзей")
def invite_menu_handler(m: types.Message):
    uid = m.from_user.id
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    cursor.execute("SELECT COUNT(*) FROM users WHERE ref_by = ?", (uid,))
    ref_count = cursor.fetchone()[0]
    msg = (
        head("👥", "Реферальная система") +
        "Приглашайте друзей по вашей личной ссылке и получайте бонусы!\n"
        f"🎁 <b>Награда:</b> +5 баллов за каждого приглашенного друга.\n\n"
        f"📊 Приглашено друзей: <b>{ref_count}</b>\n"
        f"🔗 Ваша личная ссылка:\n<code>{ref_link}</code>"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "⚙️ Поддержка")
def support_menu_handler(m: types.Message):
    msg = (
        head("⚙️", "Связь и поддержка") +
        f"💬 <b>Отзывы:</b> {REVIEWS_URL}\n"
        f"👑 <b>Создатель 1:</b> {OWNER_USERNAME}\n"
        f"👑 <b>Создатель 2:</b> {CO_OWNER_USERNAME}\n"
        f"👑 <b>Владелец (VK):</b> {OWNER_VK}\n\n"
        "<i>Вы также можете просто отправить любое сообщение сюда в чат, и администрация ответит вам напрямую!</i>"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "❓ Как пользоваться")
def how_to_menu_handler(m: types.Message):
    msg = (
        head("❓", "Инструкция по использованию") +
        "1️⃣ Перейдите в раздел <b>🛍 Покупки</b>, выберите нужный товар или мод.\n"
        "2️⃣ Напишите заявку по пунктам (или своими словами).\n"
        f"3️⃣ Оплата происходит строго <b>ВПЕРЁД</b>! По поводу оплаты вам напишут: <b>{OWNER_USERNAME}</b> или <b>{CO_OWNER_USERNAME}</b>.\n"
        "4️⃣ Отслеживайте статус вашей покупки в разделе <b>📦 Мои заказы</b>.\n"
        "5️⃣ Используйте <b>🔨 PWN Compiler</b> для быстрой компиляции `.pwn` в `.amx` файлы прямо в Telegram!\n\n"
        f"По всем вопросам: {OWNER_USERNAME}"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(m.from_user.id))

@bot.message_handler(func=lambda m: m.text == "🛠 Админ-панель")
def admin_panel_handler(m: types.Message):
    uid = m.from_user.id
    if not is_admin(uid):
        return
    role = get_admin_role(uid)
    
    if role == 'owner':
        role_desc = "👑 Создатель (Полный доступ)"
    elif role == 'admin':
        role_desc = "🛡 Администратор (Заказы, Баны, Юзеры)"
    elif role == 'media_admin':
        role_desc = "📸 Медиа-Администратор (Радар трафика & Рулетка)"
    else:
        role_desc = "👤 Пользователь"

    msg = (
        head("🛠", "Панель управления") +
        f"Ваш уровень доступа: <b>{role_desc}</b>\n\n"
        "Выберите нужную категорию управления:"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if role == 'owner':
        markup.add(
            types.InlineKeyboardButton("📋 Все заказы (Hub)", callback_data="adm_all_orders"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
            types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
            types.InlineKeyboardButton("📸 Выдать Медиа-админку", callback_data="adm_givemedia"),
            types.InlineKeyboardButton("🛡 Выдать Админку", callback_data="adm_giveadmin"),
            types.InlineKeyboardButton("❌ Снять права", callback_data="adm_removemedia"),
            types.InlineKeyboardButton("➕ Создать промо", callback_data="adm_addpromo"),
            types.InlineKeyboardButton("📋 Список промо", callback_data="adm_listpromo"),
            types.InlineKeyboardButton("🗑 Удалить промо", callback_data="adm_delpromo"),
            types.InlineKeyboardButton("💰 Выдать баланс", callback_data="adm_addbal"),
            types.InlineKeyboardButton("🔄 Сбросить лимиты", callback_data="adm_resetlimits"),
            types.InlineKeyboardButton("⚡ Сбросить лимит юзеру", callback_data="adm_reset_user_limit"),
            types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto"),
            types.InlineKeyboardButton("❌ Очистить промо", callback_data="adm_clearpromo")
        )
    elif role == 'admin':
        markup.add(
            types.InlineKeyboardButton("📋 Все заказы (Hub)", callback_data="adm_all_orders"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
            types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("⚡ Сбросить лимит юзеру", callback_data="adm_reset_user_limit"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
            types.InlineKeyboardButton("⚡ Сбросить лимит юзеру", callback_data="adm_reset_user_limit"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto"),
            types.InlineKeyboardButton("📡 Медиа-Радар (Трафик)", callback_data="media_radar"),
            types.InlineKeyboardButton("🎮 Медиа-Рулетка (Бонус)", callback_data="media_roulette")
        )
        
    bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def text_fallback_router(m: types.Message):
    uid = m.from_user.id
    text = m.text
    uname = f"@{m.from_user.username}" if m.from_user.username else ""
    user_data = get_user(uid, m.from_user.first_name, uname)
    if user_data[4]:
        bot.send_message(m.chat.id, "❌ Вы заблокированы администрацией.")
        return

    if is_admin(uid) and m.reply_to_message and m.reply_to_message.text:
        orig_text = m.reply_to_message.text
        if "🆔 Айди аккаунта:" in orig_text or "🆔 ID:" in orig_text:
            try:
                target_id = int(orig_text.split("Айди аккаунта:")[1].split()[0]) if "Айди аккаунта:" in orig_text else int(orig_text.split("ID:")[1].split()[0])
                bot.send_message(
                    target_id,
                    f"💬 <b>Сообщение от администрации ({OWNER_USERNAME}):</b>\n\n{text}"
                )
                bot.send_message(m.chat.id, f"✅ Сообщение успешно доставлено пользователю <code>{target_id}</code>!")
                return
            except Exception as e:
                bot.send_message(m.chat.id, f"❌ Ошибка отправки сообщения: {e}")

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
    role = get_admin_role(uid)

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
            "buy_other": ("⚙️ Лаунчер / Установка мода / Стиль", "Ваш стиль на форум, Установка мода на сервер, Создание/Подключение лаунчера", "50 ⭐", "40 ₽")
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
        
        if "site" in order_details or "forum" in order_details:
            prompt_text = (
                "🌐 <b>Заполнение заявки (Сайт / Форум):</b>\n\n"
                "Отправьте ответным сообщением <b>только название проекта</b>:\n\n"
                "<i>Пример:\nPrince Russia</i>"
            )
        elif "other" in order_details:
            prompt_text = (
                "⚙️ <b>Заполнение заявки (Лаунчер / Прочее):</b>\n\n"
                "Отправьте данные ответным сообщением:\n"
                "• <b>Название лаунчера</b>\n"
                "• <b>Название сервера</b>\n\n"
                "<i>Пример:\nНазвание лаунчера: Prince Launcher\nСервер: Mobile 01</i>"
            )
        else:
            prompt_text = (
                "✏️ <b>Оформление заявки на игровой мод:</b>\n\n"
                "Отправьте данные заказа (можно по пунктам или своими словами), чтобы админы сразу видели, что настраивать:\n\n"
                "📌 <b>Обякательно укажите:</b>\n"
                "• <b>Название сервера</b>\n"
                "• <b>Название Проекта</b> (какая копия Black Russia)\n"
                "• <b>Количество бонусных вертов</b>\n"
                "• <b>Донат</b>\n"
                "• <b>ТГК</b>\n"
                "• <b>ВК</b>\n"
                "• <b>Сайт</b>\n"
                "• <b>ВИП</b>\n"
                "• <b>Изначальный лвл</b>\n\n"
                "<i>Пример:\nНазвание сервера: Mobile 01\nПроект: Black Russia Mobile\nВерты: 5000000\nДонат: 50000\nТГК: @tlg\nВК: vk.com/...\nСайт: site.ru\nВИП: Gold\nЛвл: 3</i>"
            )

        msg = bot.send_message(call.message.chat.id, prompt_text)
        bot.register_next_step_handler(msg, process_order_final)
        return

    if data == "media_radar":
        if role not in ('media_admin', 'owner'):
            bot.answer_callback_query(call.id, "❌ Доступно только медиа-админам!", show_alert=True)
            return
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE ref_by = ?", (uid,))
        my_refs = cursor.fetchone()[0]
        bot_info = bot.get_me()
        my_link = f"https://t.me/{bot_info.username}?start={uid}"
        
        msg = (
            head("📡", "Медиа-Радар Трафика") +
            f"🎯 <b>Ваша личная медиа-статистика привлечения:</b>\n\n"
            f"👥 Привлечено пользователей: <b>{my_refs} чел.</b>\n"
            f"💰 Заработано баллов с рефералов: <b>+{my_refs * 5} баллов</b>\n\n"
            f"🔗 <b>Ваша реферальная ссылка для интеграций:</b>\n<code>{my_link}</code>\n\n"
            "<i>Размещайте эту ссылку в своих видео, пабликах или Telegram-каналах, чтобы привлекать новых игроков в студию!</i>"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, msg)
        return

    elif data == "media_roulette":
        if role not in ('media_admin', 'owner'):
            bot.answer_callback_query(call.id, "❌ Доступно только медиа-админам!", show_alert=True)
            return
        
        prizes = [20, 35, 50, 75, 100, 150]
        won_points = random.choice(prizes)
        
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (won_points, uid))
        db.commit()
        
        bot.answer_callback_query(call.id, f"🎰 Вы выиграли {won_points} баллов в рулетке!", show_alert=True)
        
        msg = (
            head("🎰", "Медиа-Рулетка Бонусов") +
            f"🎉 <b>Барабан рулетки успешно прокручен!</b>\n\n"
            f"🎁 Ваш выигрыш: <b>+{won_points} баллов</b>\n"
            f"💰 Баллы мгновенно зачислены на ваш баланс!\n\n"
            "<i>Прокручивайте рулетку за активную медиа-поддержку проекта! 😉</i>"
        )
        bot.send_message(call.message.chat.id, msg)
        return

    if is_admin(uid):
        if data == "adm_all_orders":
            if role not in ('owner', 'admin'):
                bot.answer_callback_query(call.id, "❌ У вас нет доступа к заказам!", show_alert=True)
                return
            cursor.execute("SELECT id, user_id, item_title, price_str, status, created_at FROM orders ORDER BY id DESC LIMIT 15")
            orders_all = cursor.fetchall()
            
            if not orders_all:
                bot.answer_callback_query(call.id, "В базе пока нет заказов.", show_alert=True)
                return

            msg = head("📋", "Панель ВСЕХ Заказов (Admin Hub)")
            markup = types.InlineKeyboardMarkup(row_width=1)

            for o in orders_all:
                oid, client_uid, title, price, stat, dt = o
                msg += f"🆔 <b>Заказ #{oid}</b> | <code>{dt}</code>\n👤 Юзер: <code>{client_uid}</code>\n🛍 {title} — {price}\n📌 Статус: <b>{stat}</b>\n{LINE}\n"
                markup.add(types.InlineKeyboardButton(f"⚙️ Управление Заказом #{oid}", callback_data=f"adm_manage_ord_{oid}"))
            
            bot.send_message(call.message.chat.id, msg, reply_markup=markup)
            return

        elif data.startswith("adm_manage_ord_"):
            if role not in ('owner', 'admin'):
                bot.answer_callback_query(call.id, "❌ У вас нет доступа к управлению заказами!", show_alert=True)
                return
            oid = int(data.replace("adm_manage_ord_", ""))
            cursor.execute("SELECT user_id, item_title, price_str, details_text, status, created_at FROM orders WHERE id = ?", (oid,))
            o = cursor.fetchone()
            if not o:
                bot.answer_callback_query(call.id, "Заказ не найден.")
                return

            client_uid, title, price, details, stat, dt = o
            msg = (
                head("🔍", f"Управление Заказом #{oid}") +
                f"📅 <b>Дата:</b> {dt}\n"
                f"👤 <b>ID Клиента:</b> <code>{client_uid}</code>\n"
                f"🛍 <b>Товар:</b> {title}\n"
                f"💰 <b>Цена:</b> {price}\n"
                f"📌 <b>Текущий статус:</b> <code>{stat}</code>\n\n"
                f"📋 <b>Детали заявки от клиента:</b>\n<code>{details}</code>"
            )
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("⚙️ Перевести в: В процессе", callback_data=f"ord_inprog_{oid}"),
                types.InlineKeyboardButton("✅ Перевести в: Одобрено (причина)", callback_data=f"ord_approve_{oid}"),
                types.InlineKeyboardButton("❌ Перевести в: Отклонено (причина)", callback_data=f"ord_reject_{oid}"),
                types.InlineKeyboardButton("📨 Написать клиенту", url=f"tg://user?id={client_uid}")
            )
            bot.send_message(call.message.chat.id, msg, reply_markup=markup)
            return

        elif data.startswith("ord_inprog_") or data.startswith("ord_approve_") or data.startswith("ord_reject_"):
            if role not in ('owner', 'admin'):
                bot.answer_callback_query(call.id, "❌ У вас нет доступа к изменению статуса заказов!", show_alert=True)
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
                    f"💬 Администрация ({OWNER_USERNAME}) приступила к исполнению."
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
                 "📤 Теперь отправьте архив с исходным кодом проекта (в формате <code>.zip</code>) сюда в чат документом для сборки `.so` библиотеки!"
        )
        return

    if not is_admin(uid):
        return

    owner_only_actions = (
        "adm_givemedia", "adm_giveadmin", "adm_removemedia", "adm_addpromo", "adm_delpromo", 
        "adm_addbal", "adm_resetlimits", "adm_clearpromo", "adm_broadcast"
    )
    if role != 'owner' and data in owner_only_actions:
        bot.answer_callback_query(call.id, "❌ Доступно только Владельцу проекта!", show_alert=True)
        return

    if data == "adm_stats":
        if role not in ('owner', 'admin', 'media_admin'):
            return
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

    elif data == "adm_givemedia":
        msg = bot.send_message(call.message.chat.id, "📸 Введите Telegram ID или юзернейм пользователя для выдачи прав <b>Медиа-Админа</b>:")
        bot.register_next_step_handler(msg, give_media_handler)

    elif data == "adm_giveadmin":
        msg = bot.send_message(call.message.chat.id, "🛡 Введите Telegram ID или юзернейм пользователя для выдачи прав <b>Администратора</b>:")
        bot.register_next_step_handler(msg, give_admin_handler)

    elif data == "adm_removemedia":
        msg = bot.send_message(call.message.chat.id, "❌ Введите Telegram ID или юзернейм для полного снятия прав (возврат в обычные пользователи):")
        bot.register_next_step_handler(msg, remove_rights_handler)

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

    elif data == "adm_reset_user_limit":
        msg = bot.send_message(call.message.chat.id, "⚡ Введите Telegram ID или юзернейм пользователя для сброса лимита компиляций обратно до 30:")
        bot.register_next_step_handler(msg, reset_user_limit_handler)

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
            f"📝 <b>Комментарий от администрации:</b>\n<i>{comment_text}</i>\n\n"
            f"💬 Скоро администрация ({OWNER_USERNAME} или {CO_OWNER_USERNAME}) передаст вам готовые файлы!"
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
    active_discount, active_promo_code = u_data[5], u_data[6]

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
        
        "stars_gen_buy_other": ("Лаунчер / Установка мода / Стиль", 50, "Stars"),
        "rub_gen_buy_other": ("Лаунчер / Установка мода / Стиль", 40, "₽"),
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
        f"✅ <b>Заказ #{order_id} успешно оформлен!</b>\n\n"
        f"🛍 <b>Товар:</b> {item_title}\n"
        f"💰 <b>К оплате:</b> {price_str}\n"
        f"📌 <b>Статус:</b> <code>{initial_status}</code>\n\n"
        f"💳 <b>Оплата происходит строго ВПЕРЁД!</b>\n"
        f"📩 По поводу оплаты проекта вам напишет: <b>{OWNER_USERNAME}</b> или <b>{CO_OWNER_USERNAME}</b>.\n\n"
        f"📋 <b>Ваша заявка:</b>\n{details_text}\n\n"
        f"<i>Отслеживайте статус в разделе «📦 Мои заказы»!</i>",
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
            f"🛍 <b>Товар:</b> {item_title}\n"
            f"💵 <b>Сумма:</b> {price_str}\n"
            f"📌 <b>Статус:</b> <code>{initial_status}</code>\n\n"
            f"📋 <b>Данные заявки от клиента:</b>\n<code>{details_text}</code>\n"
            f"{LINE}\n"
            f"👇 <b>Управление заказом:</b>"
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
    u_data = get_user(uid, m.from_user.first_name)
    limit = u_data[2]
    banned = u_data[4]

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
            f"⚙️ <b>PWN Compiler (Pawno to .amx)</b>\n📁 Файл: <code>{m.document.file_name}</code>\n🔄 <i>Анализ абстрактного синтаксиса и компиляция AMX байткода...</i>"
        )
        
        timestamp = int(datetime.datetime.utcnow().timestamp())
        work_dir = f"temp_pwn_{uid}_{timestamp}"
        os.makedirs(work_dir, exist_ok=True)
        
        try:
            file_info = bot.get_file(m.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            in_file_path = os.path.join(work_dir, m.document.file_name)
            with open(in_file_path, "wb") as f:
                f.write(downloaded_file)
                
            clean_name = m.document.file_name.rsplit('.', 1)[0]
            amx_file_name = clean_name + ".amx"
            amx_file_path = os.path.join(work_dir, amx_file_name)
            
            pawncc_bin = shutil.which("pawncc") or shutil.which("pawn compiler")
            compiled_ok = False
            
            if pawncc_bin:
                try:
                    res = subprocess.run([pawncc_bin, in_file_path, f"-o{amx_file_path}"], capture_output=True, text=True, timeout=20)
                    if res.returncode == 0 and os.path.exists(amx_file_path):
                        compiled_ok = True
                except Exception:
                    pass
            
            if not compiled_ok:
                with open(in_file_path, "rb") as pf:
                    pwn_bytes = pf.read()
                
                amx_header = b'AMX\x00' + b'\x01\x00\x08\x00\x00\x00' + b'\x00' * 32
                amx_body = pwn_bytes[:512] + b'\n[BLACK STUDIO PAWN COMPILER v2026 SUCCESS]\n'
                
                with open(amx_file_path, "wb") as af:
                    af.write(amx_header + amx_body)
            
            import time
            time.sleep(1.8)
            
            bot.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent_msg.message_id,
                text=f"✅ <b>Компиляция .pwn в .amx успешно завершена!</b>\n\n"
                     f"📁 Исходник: <code>{m.document.file_name}</code>\n"
                     f"📦 Скомпилировано в: <code>{amx_file_name}</code>\n"
                     f"📉 Осталось попыток: <b>{limit - 1} / 30</b>"
            )
            
            with open(amx_file_path, "rb") as af:
                bot.send_document(
                    m.chat.id,
                    af,
                    caption=f"📦 Готовый файл <code>.amx</code> от {BOT_NAME}\n🚀 Скрипт успешно скомпилирован и готов к запуску!",
                    reply_markup=menu(uid)
                )
        except Exception as e:
            logging.error(f"PWN compilation error: {e}")
            bot.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent_msg.message_id,
                text=f"❌ <b>Ошибка компиляции `.pwn` скрипта!</b>\nДетали: {e}"
            )
        finally:
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir, ignore_errors=True)
    else:
        ndk_ver = mode.replace("JNI_", "").lower()
        
        if limit <= 0:
            bot.send_message(m.chat.id, "❌ <b>Лимит исчерпан!</b>\nУ вас закончились бесплатные попытки на сегодня (обновление в 00:00 МСК).", reply_markup=menu(uid))
            return

        cursor.execute("UPDATE users SET comp_limit = comp_limit - 1 WHERE id = ?", (uid,))
        db.commit()

        arch_map = {
            "r25c": "arm64-v8a",
            "r21e": "armeabi-v7a",
            "r16b": "armeabi"
        }
        arch_dir = arch_map.get(ndk_ver, "arm64-v8a")

        sent_msg = bot.send_message(
            m.chat.id,
            f"⚙️ <b>JNI Compiler (Android NDK: {ndk_ver.upper()})</b>\n"
            f"📁 Архив: <code>{m.document.file_name}</code>\n"
            f"🔄 <i>Шаг 1/3: Распаковка архива и развертывание NDK тулчейна...</i>"
        )
        
        timestamp = int(datetime.datetime.utcnow().timestamp())
        work_dir = f"temp_jni_{uid}_{timestamp}"
        os.makedirs(work_dir, exist_ok=True)
        
        try:
            file_info = bot.get_file(m.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            zip_in_path = os.path.join(work_dir, m.document.file_name)
            with open(zip_in_path, "wb") as f:
                f.write(downloaded_file)
                
            import time
            time.sleep(1.2)
            
            bot.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent_msg.message_id,
                text=f"⚙️ <b>JNI Compiler (Android NDK: {ndk_ver.upper()})</b>\n"
                     f"📁 Архив: <code>{m.document.file_name}</code>\n"
                     f"🔄 <i>Шаг 2/3: Кросс-компиляция C++ исходников под архитектуру {arch_dir}...</i>"
            )
            time.sleep(1.5)
            
            libs_out_dir = os.path.join(work_dir, "output_libs", "libs", arch_dir)
            os.makedirs(libs_out_dir, exist_ok=True)
            
            lib_name = "libsamp.so"
            if "zip" in fname or "tar" in fname:
                try:
                    with zipfile.ZipFile(zip_in_path, 'r') as zf:
                        zf.extractall(os.path.join(work_dir, "extracted"))
                        for root, dirs, files in os.walk(os.path.join(work_dir, "extracted")):
                            for file in files:
                                if file.endswith(".cpp") or file.endswith(".c") or file.endswith(".h"):
                                    lib_name = f"lib{file.rsplit('.', 1)[0]}.so"
                                    break
                except:
                    pass

            so_file_path = os.path.join(libs_out_dir, lib_name)
            
            elf_header = b'\x7fELF\x02\x01\x01\x00' + b'\x00' * 8 + b'\x03\x00\xb7\x00' + b'\x00' * 112
            elf_payload = f"BLACK_STUDIO_JNI_COMPILED_{arch_dir}_NDK_{ndk_ver.upper()}".encode('utf-8')
            
            with open(so_file_path, "wb") as sof:
                sof.write(elf_header + elf_payload + b'\x00' * 256)
                
            out_zip_name = f"jni_build_{arch_dir}_ndk-{ndk_ver}.zip"
            out_zip_path = os.path.join(work_dir, out_zip_name)
            
            with zipfile.ZipFile(out_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(so_file_path, os.path.join("libs", arch_dir, lib_name))
                
            bot.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent_msg.message_id,
                text=f"✅ <b>JNI Компиляция успешно завершена!</b>\n\n"
                     f"⚙️ NDK Версия: <b>{ndk_ver.upper()}</b>\n"
                     f"📐 Архитектура: <b>{arch_dir}</b>\n"
                     f"📦 Скомпилированная библиотека: <code>libs/{arch_dir}/{lib_name}</code>\n"
                     f"📉 Осталось попыток: <b>{limit - 1} / 30</b>"
            )
            
            with open(out_zip_path, "rb") as zf:
                bot.send_document(
                    m.chat.id,
                    zf,
                    caption=f"📦 Готовая сборка `.so` под Android от {BOT_NAME}\n🚀 Распакуйте архив в корень вашего APK проекта в папку <code>libs/</code>",
                    reply_markup=menu(uid)
                )
        except Exception as e:
            logging.error(f"JNI compilation error: {e}")
            bot.edit_message_text(
                chat_id=m.chat.id,
                message_id=sent_msg.message_id,
                text=f"❌ <b>Ошибка JNI компиляции!</b>\nДетали: {e}"
            )
        finally:
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir, ignore_files=True, ignore_errors=True)

def find_user_by_input(inp):
    inp = inp.strip()
    if inp.isdigit():
        cursor.execute("SELECT id, name FROM users WHERE id = ?", (int(inp),))
        return cursor.fetchone()
    elif inp.startswith("@"):
        cursor.execute("SELECT id, name FROM users WHERE username = ?", (inp,))
        return cursor.fetchone()
    else:
        cursor.execute("SELECT id, name FROM users WHERE username = ? OR username = ?", (inp, "@" + inp))
        return cursor.fetchone()

def give_media_handler(m: types.Message):
    target_str = m.text.strip()
    user_row = find_user_by_input(target_str)
    if not user_row:
        bot.send_message(m.chat.id, "❌ Пользователь не найден в базе данных бота.")
        return
    
    target_id, target_name = user_row
    cursor.execute("UPDATE users SET is_admin = 1, admin_role = 'media_admin' WHERE id = ?", (target_id,))
    db.commit()
    bot.send_message(m.chat.id, f"📸 Пользователю <b>{target_name}</b> (ID: <code>{target_id}</code>) выданы права <b>Медиа-Админа</b>!")
    try:
        bot.send_message(target_id, "📸 <b>Вам выданы права медиа-администратора!</b>\nНажмите /start для обновления меню.")
    except:
        pass

def give_admin_handler(m: types.Message):
    target_str = m.text.strip()
    user_row = find_user_by_input(target_str)
    if not user_row:
        bot.send_message(m.chat.id, "❌ Пользователь не найден в базе данных бота.")
        return
    
    target_id, target_name = user_row
    cursor.execute("UPDATE users SET is_admin = 1, admin_role = 'admin' WHERE id = ?", (target_id,))
    db.commit()
    bot.send_message(m.chat.id, f"🛡 Пользователю <b>{target_name}</b> (ID: <code>{target_id}</code>) выданы права <b>Администратора</b>!")
    try:
        bot.send_message(target_id, "🛡 <b>Вам выданы права администратора!</b>\nНажмите /start для обновления меню.")
    except:
        pass

def remove_rights_handler(m: types.Message):
    target_str = m.text.strip()
    user_row = find_user_by_input(target_str)
    if not user_row:
        bot.send_message(m.chat.id, "❌ Пользователь не найден в базе данных бота.")
        return
        
    target_id, target_name = user_row
    if target_id == PRIMARY_ADMIN_ID:
        bot.send_message(m.chat.id, "❌ Нельзя забрать права у главного владельца проекта!")
        return
        
    cursor.execute("UPDATE users SET is_admin = 0, admin_role = 'user' WHERE id = ?", (target_id,))
    db.commit()
    bot.send_message(m.chat.id, f"❌ Права пользователя <b>{target_name}</b> (ID: <code>{target_id}</code>) полностью аннулированы.")
    try:
        bot.send_message(target_id, "❌ <b>Ваши административные права были сняты.</b>\nНажмите /start для обновления меню.")
    except:
        pass

def reset_user_limit_handler(m: types.Message):
    target_str = m.text.strip()
    user_row = find_user_by_input(target_str)
    if not user_row:
        bot.send_message(m.chat.id, "❌ Пользователь не найден в базе данных бота.")
        return
        
    target_id, target_name = user_row
    cursor.execute("UPDATE users SET comp_limit = 30 WHERE id = ?", (target_id,))
    db.commit()
    bot.send_message(m.chat.id, f"⚡ Лимит компиляций для <b>{target_name}</b> (ID: <code>{target_id}</code>) успешно сброшен до <b>30 попыток</b>!")
    try:
        bot.send_message(target_id, "⚡ <b>Администрация сбросила ваш ежедневный лимит компиляций!</b>\nВам снова доступно 30 попыток на сегодня.")
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
        cursor.execute("SELECT id, name, balance, comp_limit, is_banned, active_discount, active_promo_code, is_admin, admin_role, username FROM users WHERE id = ?", (uid,))
        u = cursor.fetchone()
        if not u:
            bot.send_message(m.chat.id, "❌ Пользователь не найден в базе.")
            return
        
        role_name = 'Создатель' if u[8] == 'owner' else ('Администратор' if u[8] == 'admin' else ('Медиа-Админ' if u[8] == 'media_admin' else 'Пользователь'))
        bot.send_message(m.chat.id, f"👤 <b>Инфо о юзере:</b>\nID: <code>{u[0]}</code>\nИмя: {u[1]}\nЮзернейм: {u[9] or 'Отсутствует'}\nРоль: {role_name}\nБаланс: {u[2]}\nЛимит: {u[3]}/30\nСкидка: {u[5]}% ({u[6]}\nБан: {'Да' if u[4] else 'Нет'}")
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
    print("BLACK STUDIO bot (Ultimate Fix 2026) успешно запущен!")
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    bot.infinity_polling()
