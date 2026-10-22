# -*- coding: utf-8 -*-
"""
BLACK STUDIO SHOP — Ultimate Inline Start & Menu Edition 2026
"""
import os
import sys
import sqlite3
import datetime
import logging
import shutil
import subprocess
import zipfile
import threading
import random
import time
from flask import Flask
from telebot import TeleBot, types

BOT_TOKEN = "8889779796:AAGpopudNLm0SZhP-1SV3VKDhwyaOKIZ7F4"
PRIMARY_ADMIN_ID = 8543358373
OWNER_USERNAME = "@Evgenn010"
CO_OWNER_USERNAME = "@forever10002"
OWNER_VK = "vk.ru/evgenn09"
REVIEWS_URL = "https://t.me/BlackSTUDIOotziv"
BOT_NAME = "BLACK STUDIO SHOP"

LINE = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

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
    is_unlimited INTEGER DEFAULT 0,
    last_reset TEXT,
    is_banned INTEGER DEFAULT 0,
    active_discount INTEGER DEFAULT 0,
    active_promo_code TEXT DEFAULT '',
    is_admin INTEGER DEFAULT 0,
    admin_role TEXT DEFAULT 'user',
    notified_reg INTEGER DEFAULT 0
)
""")

try:
    cursor.execute("SELECT is_unlimited FROM users LIMIT 1")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE users ADD COLUMN is_unlimited INTEGER DEFAULT 0")
    db.commit()

try:
    cursor.execute("SELECT balance FROM users LIMIT 1")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 0")
    db.commit()

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

def get_user(uid, name="User", username=""):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT id, balance, comp_limit, is_unlimited, last_reset, is_banned, active_discount, active_promo_code, is_admin, admin_role, notified_reg FROM users WHERE id = ?", (uid,))
    row = cursor.fetchone()
    
    if not row:
        admin_flag = 1 if uid == PRIMARY_ADMIN_ID else 0
        role = 'owner' if uid == PRIMARY_ADMIN_ID else 'user'
        cursor.execute("INSERT INTO users (id, name, username, balance, last_reset, active_discount, active_promo_code, is_admin, admin_role, notified_reg) VALUES (?, ?, ?, 0, ?, 0, '', ?, ?, 0)", (uid, name, username, today, admin_flag, role))
        db.commit()
        return (uid, 0, 30, 0, 0, 0, '', admin_flag, role, 0)
    else:
        user_id, balance, comp_limit, is_unlimited, last_reset, is_banned, active_discount, active_promo_code, admin_flag, admin_role, notified_reg = row
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
            return (user_id, balance, 30, is_unlimited, is_banned, active_discount, active_promo_code, admin_flag, admin_role, notified_reg)
        return (user_id, balance, comp_limit, is_unlimited, is_banned, active_discount, active_promo_code, admin_flag, admin_role, notified_reg)

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

# Reply клавиатура под текстом
def menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍 Каталог Проектов"),
        types.KeyboardButton("📦 Мои Заказы"),
        types.KeyboardButton("👤 Мой Профиль"),
        types.KeyboardButton("🎟 Промокод"),
        types.KeyboardButton("🔨 PWN Compiler"),
        types.KeyboardButton("⚙️ JNI Compiler"),
        types.KeyboardButton("🛠 Тех. Поддержка"),
        types.KeyboardButton("📜 Правила & FAQ"),
        types.KeyboardButton("🌐 Наши Ресурсы")
    )
    if is_admin(uid):
        markup.add(types.KeyboardButton("⚡ ПАНЕЛЬ ОЛИГАРХА (Админ)"))
    return markup

# Inline клавиатура для сообщения /start
def get_start_inline_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛍 Каталог Проектов", callback_data="menu_shop"),
        types.InlineKeyboardButton("📦 Мои Заказы", callback_data="menu_orders"),
        types.InlineKeyboardButton("👤 Мой Профиль", callback_data="menu_profile"),
        types.InlineKeyboardButton("🎟 Промокод", callback_data="menu_promo"),
        types.InlineKeyboardButton("🔨 PWN Compiler", callback_data="menu_pwn"),
        types.InlineKeyboardButton("⚙️ JNI Compiler", callback_data="menu_jni"),
        types.InlineKeyboardButton("🛠 Тех. Поддержка", callback_data="menu_support"),
        types.InlineKeyboardButton("📜 Правила & FAQ", callback_data="menu_rules"),
        types.InlineKeyboardButton("🌐 Наши Ресурсы", callback_data="menu_resources")
    )
    if is_admin(uid):
        markup.add(types.InlineKeyboardButton("⚡ ПАНЕЛЬ ОЛИГАРХА (Админ)", callback_data="menu_admin"))
    return markup

def head(emoji, title):
    return f"{emoji} <b>{title}</b>\n{LINE}\n\n"

@bot.message_handler(commands=["start"])
def start_cmd(m: types.Message):
    u = m.from_user
    user_temp_mode.pop(u.id, None)
    uname = f"@{u.username}" if u.username else ""
    user_data = get_user(u.id, u.first_name, uname)
    banned = user_data[4]
    notified_reg = user_data[9]
    
    if banned:
        bot.send_message(m.chat.id, "❌ Вы заблокированы в этом боте.")
        return

    if u.id != PRIMARY_ADMIN_ID and not notified_reg:
        try:
            username_str = f"@{u.username}" if u.username else "Отсутствует"
            reg_alert = (
                f"👤 <b>НОВЫЙ ПОКУПАТЕЛЬ В БОТЕ!</b>\n"
                f"{LINE}\n"
                f"👤 <b>Имя:</b> {u.full_name}\n"
                f"🔗 <b>Юзернейм:</b> {username_str}\n"
                f"🆔 <b>ID:</b> <code>{u.id}</code>\n"
                f"{LINE}"
            )
            bot.send_message(PRIMARY_ADMIN_ID, reg_alert)
            cursor.execute("UPDATE users SET notified_reg = 1 WHERE id = ?", (u.id,))
            db.commit()
        except Exception as e:
            logging.error(f"Error: {e}")

    text = (
        f"👑 <b>BLACK STUDIO SHOP — GOD MODE ENGINE 🔥</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"Официальный бот высшей пробы. Продажа готовых CRMP/SA-MP сборок, форумов, сайтов, лаунчеров и компиляция скриптов!\n\n"
        f"<b>Выберите нужный раздел кнопками ниже:</b>"
    )
    bot.send_message(m.chat.id, text, reply_markup=get_start_inline_menu(u.id))
    # Также дублируем Reply-клавиатуру внизу для полного удобства
    bot.send_message(m.chat.id, "👇 Основная клавиатура активирована:", reply_markup=menu(u.id))

# ==================== ЭКСКЛЮЗИВНЫЕ КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦА ====================

@bot.message_handler(commands=["owner", "crown"])
def owner_secret_menu(m: types.Message):
    if get_admin_role(m.from_user.id) != 'owner':
        return
    text = (
        f"👑 <b>СЕКРЕТНЫЙ ПУЛЬТ ВЛАДЕЛЬЦА BLACK STUDIO SHOP</b>\n{LINE}\n"
        f"⚡ <code>/dump_db</code> — Скачать файл базы данных nexus.db\n"
        f"⚡ <code>/unlimit ID</code> — Выдать бесконечный лимит компиляций\n"
        f"⚡ <code>/vip_all СКИДКА</code> — Глобальная скидка всем пользователям\n"
        f"⚡ <code>/clear_orders</code> — Очистить всю историю заказов\n"
        f"⚡ <code>/sql ЗАПРОС</code> — Выполнить прямой SQL запрос в БД\n"
        f"⚡ <code>/bot_restart</code> — Перезапустить бота"
    )
    bot.send_message(m.chat.id, text)

@bot.message_handler(commands=["dump_db"])
def dump_db_cmd(m: types.Message):
    if get_admin_role(m.from_user.id) != 'owner':
        return
    if os.path.exists("nexus.db"):
        with open("nexus.db", "rb") as doc:
            bot.send_document(m.chat.id, doc, caption="💾 Резервная копия базы данных nexus.db")

@bot.message_handler(commands=["unlimit"])
def unlimit_cmd(m: types.Message):
    if get_admin_role(m.from_user.id) != 'owner':
        return
    try:
        parts = m.text.split()
        target_id = int(parts[1])
        cursor.execute("UPDATE users SET is_unlimited = 1 WHERE id = ?", (target_id,))
        db.commit()
        bot.send_message(m.chat.id, f"♾ Бесконечный лимит выдан юзеру {target_id}!")
    except:
        bot.send_message(m.chat.id, "❌ Пример: <code>/unlimit 123456789</code>")

@bot.message_handler(commands=["vip_all"])
def vip_all_cmd(m: types.Message):
    if get_admin_role(m.from_user.id) != 'owner':
        return
    try:
        disc = int(m.text.split()[1])
        cursor.execute("UPDATE users SET active_discount = ?, active_promo_code = 'SALE'", (disc,))
        db.commit()
        bot.send_message(m.chat.id, f"🎉 Всем пользователям выдана скидка {disc}%!")
    except:
        bot.send_message(m.chat.id, "❌ Пример: <code>/vip_all 20</code>")

@bot.message_handler(commands=["clear_orders"])
def clear_orders_cmd(m: types.Message):
    if get_admin_role(m.from_user.id) != 'owner':
        return
    cursor.execute("DELETE FROM orders")
    db.commit()
    bot.send_message(m.chat.id, "🧹 История заказов очищена!")

@bot.message_handler(commands=["sql"])
def sql_execute_cmd(m: types.Message):
    if get_admin_role(m.from_user.id) != 'owner':
        return
    q = m.text.replace("/sql", "").strip()
    try:
        cursor.execute(q)
        db.commit()
        bot.send_message(m.chat.id, f"✅ SQL Выполнен: {cursor.fetchall()[:5]}")
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ SQL Ошибка: {e}")

@bot.message_handler(commands=["bot_restart"])
def restart_bot_cmd(m: types.Message):
    if get_admin_role(m.from_user.id) != 'owner':
        return
    bot.send_message(m.chat.id, "🔄 Перезапуск бота...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==================== ОБРАБОТЧИКИ КНОПОК МЕНЮ ====================

@bot.message_handler(func=lambda m: m.text in ("🛍 Каталог Проектов", "🛍 Покупки"))
def shop_handler(m: types.Message):
    uid = m.from_user.id
    user_temp_mode.pop(uid, None)
    u_data = get_user(uid, m.from_user.first_name)
    active_discount, active_promo_code = int(u_data[6] or 0), u_data[7]
    disc_text = f"\n🔥 <i>Активна скидка {active_discount}% ({active_promo_code})!</i>" if active_discount > 0 else ""
    msg = (
        head("🛍", "Каталог Проектов и Сборок") +
        f"Выберите интересующий проект или услугу:{disc_text}"
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

@bot.message_handler(func=lambda m: m.text in ("📦 Мои Заказы", "📦 Заказы"))
def orders_handler(m: types.Message):
    uid = m.from_user.id
    user_temp_mode.pop(uid, None)
    cursor.execute("SELECT id, item_title, price_str, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 10", (uid,))
    orders_list = cursor.fetchall()
    if not orders_list:
        bot.send_message(m.chat.id, head("📦", "Ваши Заказы") + "У вас пока нет оформленных заказов.", reply_markup=menu(uid))
        return
        
    msg = head("📦", "История Заказов")
    for o in orders_list:
        msg += f"📑 <b>Заказ #{o[0]}</b> | {o[4]}\n🛍 <b>Товар:</b> {o[1]}\n💵 <b>Сумма:</b> {o[2]}\n📌 <b>Статус:</b> {o[3]}\n{LINE}\n"
    bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "👤 Мой Профиль")
def profile_handler(m: types.Message):
    uid = m.from_user.id
    uname = f"@{m.from_user.username}" if m.from_user.username else ""
    u_data = get_user(uid, m.from_user.first_name, uname)
    balance, comp_limit, is_unlimited, active_discount, active_promo_code, role = u_data[1], u_data[2], u_data[3], u_data[6], u_data[7], u_data[9]
    
    limit_str = "♾ БЕСКОНЕЧНО" if is_unlimited else f"{comp_limit} / 30"
    promo_text = f"<code>{active_promo_code}</code> (-{active_discount}%)" if active_discount > 0 else "Нет"
    
    msg = (
        head("👤", "Профиль Покупателя") +
        f"🆔 <b>ID:</b> <code>{uid}</code>\n"
        f"👤 <b>Имя:</b> {m.from_user.full_name}\n"
        f"🔰 <b>Должность:</b> {role.upper()}\n"
        f"🔨 <b>Лимит компиляций на сегодня:</b> {limit_str}\n"
        f"🎟 <b>Активная скидка:</b> {promo_text}"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "🎟 Промокод")
def promo_menu_handler(m: types.Message):
    msg = bot.send_message(m.chat.id, "🎟 Введите ваш промокод на скидку в ответном сообщении:")
    bot.register_next_step_handler(msg, process_promo)

def process_promo(m: types.Message):
    uid = m.from_user.id
    code = m.text.strip().upper()
    cursor.execute("SELECT discount, max_uses, used_count FROM promo WHERE code = ?", (code,))
    promo = cursor.fetchone()
    
    if not promo:
        bot.send_message(m.chat.id, "❌ Промокод не найден!", reply_markup=menu(uid))
        return

    discount, max_uses, used_count = promo
    cursor.execute("UPDATE users SET active_discount = ?, active_promo_code = ? WHERE id = ?", (discount, code, uid))
    db.commit()
    bot.send_message(m.chat.id, f"🎉 <b>Промокод {code} активирован!</b>\nСкидка <b>{discount}%</b> применится к следующему заказу.", reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "🔨 PWN Compiler")
def pwn_menu_handler(m: types.Message):
    uid = m.from_user.id
    user_temp_mode[uid] = "PWN"
    u_data = get_user(uid, m.from_user.first_name)
    limit_str = "♾ БЕСКОНЕЧНО" if u_data[3] else f"{u_data[2]} / 30"
    msg = (
        head("🔨", "PWN Compiler (.pwn to .amx)") +
        f"Осталось попыток: <b>{limit_str}</b>\n\n"
        "📤 Отправьте файл скрипта <code>.pwn</code> в чат документом."
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "⚙️ JNI Compiler")
def jni_menu_handler(m: types.Message):
    uid = m.from_user.id
    user_temp_mode.pop(uid, None)
    msg = (
        head("⚙️", "JNI Compiler (Android NDK)") +
        "Выберите версию NDK для компиляции `.so`:"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🟢 NDK r25c · arm64-v8a", callback_data="ndk_r25c"),
        types.InlineKeyboardButton("🟡 NDK r21e · armeabi-v7a", callback_data="ndk_r21e"),
        types.InlineKeyboardButton("🔴 NDK r16b · armeabi", callback_data="ndk_r16b")
    )
    bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ("🛠 Тех. Поддержка", "🛠 Поддержка"))
def support_menu_handler(m: types.Message):
    msg = (
        head("🛠", "Техническая Поддержка") +
        f"💬 <b>Отзывы:</b> {REVIEWS_URL}\n"
        f"👑 <b>Создатель 1:</b> {OWNER_USERNAME}\n"
        f"👑 <b>Создатель 2:</b> {CO_OWNER_USERNAME}\n\n"
        "<i>Отправьте сообщение, фото, видео или GIF прямо сюда в чат, и мы ответим!</i>"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(m.from_user.id))

@bot.message_handler(func=lambda m: m.text == "📜 Правила & FAQ")
def rules_handler(m: types.Message):
    msg = (
        head("📜", "Правила и FAQ") +
        "1. Оплата за проекты и услуги происходит строго ВПЕРЁД.\n"
        "2. Гарантия работоспособности и техподдержка сборок.\n"
        "3. По всем вопросам: @Evgenn010"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(m.from_user.id))

@bot.message_handler(func=lambda m: m.text == "🌐 Наши Ресурсы")
def resources_handler(m: types.Message):
    msg = (
        head("🌐", "Наши Ресурсы") +
        f"💬 <b>Отзывы:</b> {REVIEWS_URL}\n"
        f"👑 <b>Владелец:</b> {OWNER_USERNAME}\n"
        f"🌐 <b>ВКонтакте:</b> {OWNER_VK}"
    )
    bot.send_message(m.chat.id, msg, reply_markup=menu(m.from_user.id))

@bot.message_handler(func=lambda m: m.text in ("🛠 Панель управления", "🛠 Панель Администратора", "🛠 Админ-панель", "⚡ ПАНЕЛЬ ОЛИГАРХА (Админ)"))
def admin_panel_handler(m: types.Message):
    uid = m.from_user.id
    if not is_admin(uid):
        return
    role = get_admin_role(uid)
    
    if role == 'owner':
        msg = (
            "🛠 <b>Панель управления</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            "Ваш уровень доступа: 👑 <b>Создатель (Полный доступ)</b>\n\n"
            "Выберите нужную категорию управления:"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📋 Все заказы (Hub)", callback_data="adm_all_orders"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
            types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
            types.InlineKeyboardButton("📸 Выдать Медиа-адм", callback_data="adm_givemedia"),
            types.InlineKeyboardButton("🛡 Выдать Админку", callback_data="adm_giveadmin"),
            types.InlineKeyboardButton("❌ Снять права", callback_data="adm_removeadmin"),
            types.InlineKeyboardButton("➕ Создать промо", callback_data="adm_addpromo"),
            types.InlineKeyboardButton("📋 Список промо", callback_data="adm_listpromo"),
            types.InlineKeyboardButton("🗑 Удалить промо", callback_data="adm_delpromo"),
            types.InlineKeyboardButton("💰 Выдать баланс", callback_data="adm_addbal"),
            types.InlineKeyboardButton("🔄 Сбросить лимиты", callback_data="adm_resetall_limits"),
            types.InlineKeyboardButton("⚡ Сбросить лимит ю", callback_data="adm_reset_user_limit"),
            types.InlineKeyboardButton("👤 Инфо о юзере", callback_data="adm_userinfo"),
            types.InlineKeyboardButton("🔨 Бан юзера", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔓 Разбан юзера", callback_data="adm_unban"),
            types.InlineKeyboardButton("📨 Сообщение юзеру", callback_data="adm_sendto")
        )
        markup.add(types.InlineKeyboardButton("❌ Очистить промо", callback_data="adm_clearpromo"))
        bot.send_message(m.chat.id, msg, reply_markup=markup)
    elif role in ('media_admin', 'media'):
        bot.send_message(m.chat.id, "❌ <b>Доступ заблокирован!</b>\nУ должности Медиа-Администратор нет доступа к рассылкам и заказам шопа.")
    else:
        bot.send_message(m.chat.id, "❌ У вас нет доступа к Панели управления.")

# ==================== CALLBACKS ====================

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call: types.CallbackQuery):
    uid = call.from_user.id
    data = call.data
    role = get_admin_role(uid)

    # Обработка нажатий на инлайн-меню из сообщения /start
    if data == "menu_shop":
        return shop_handler(call.message)
    elif data == "menu_orders":
        return orders_handler(call.message)
    elif data == "menu_profile":
        return profile_handler(call.message)
    elif data == "menu_promo":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🎟 Введите ваш промокод на скидку в ответном сообщении:")
        bot.register_next_step_handler(msg, process_promo)
        return
    elif data == "menu_pwn":
        return pwn_menu_handler(call.message)
    elif data == "menu_jni":
        return jni_menu_handler(call.message)
    elif data == "menu_support":
        return support_menu_handler(call.message)
    elif data == "menu_rules":
        return rules_handler(call.message)
    elif data == "menu_resources":
        return resources_handler(call.message)
    elif data == "menu_admin":
        return admin_panel_handler(call.message)

    if data.startswith("buy_"):
        items = {
            "buy_br2026": ("Black Russia 2025-2026 (с планшетом)", "140 ⭐ / 100-150 ₽"),
            "buy_br2025": ("Black Russia 2025 (без планшета)", "120 ⭐ / 60-90 ₽"),
            "buy_br2025_robots": ("Black Russia 2025 (роботы фулл)", "100 ⭐ / 80-130 ₽"),
            "buy_radmir": ("Мод Радмир 8.4 (ПК)", "100 ⭐ / 90-150 ₽"),
            "buy_forum": ("Готовый Форум", "50 ⭐ / 40 ₽"),
            "buy_site": ("Готовый Сайт", "50 ⭐ / 38 ₽"),
            "buy_other": ("Лаунчер / Установка мода / Стиль", "50 ⭐ / 40 ₽")
        }
        title, price = items.get(data, ("Проект", "100 ₽"))
        user_order_step[uid] = title
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"✏️ <b>Оформление заказа: {title}</b>\n\nУкажите детали заказа в ответном сообщении:")
        bot.register_next_step_handler(msg, process_order_final)
        return

    if role in ('media_admin', 'media') and (data == "adm_all_orders" or data == "adm_broadcast"):
        bot.answer_callback_query(call.id, "❌ У Медиа-Админа нет доступа к этой функции!", show_alert=True)
        return

    if role == 'owner':
        if data == "adm_all_orders":
            cursor.execute("SELECT id, user_id, item_title, price_str, status, created_at FROM orders ORDER BY id DESC LIMIT 15")
            orders = cursor.fetchall()
            if not orders:
                bot.answer_callback_query(call.id, "Заказов пока нет.", show_alert=True)
                return
            msg = head("📋", "Все Заказы (Hub)")
            markup = types.InlineKeyboardMarkup(row_width=1)
            for o in orders:
                msg += f"🆔 <b>Заказ #{o[0]}</b> | {o[5]}\n👤 Юзер: <code>{o[1]}</code>\n🛍 {o[2]} — {o[3]}\n📌 Статус: <b>{o[4]}</b>\n{LINE}\n"
                markup.add(types.InlineKeyboardButton(f"⚙️ Управление Заказом #{o[0]}", callback_data=f"adm_ord_{o[0]}"))
            bot.send_message(call.message.chat.id, msg, reply_markup=markup)
            return

        elif data == "adm_stats":
            cursor.execute("SELECT COUNT(*) FROM users")
            u_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM orders")
            o_count = cursor.fetchone()[0]
            bot.answer_callback_query(call.id, f"Пользователей: {u_count} | Заказов: {o_count}", show_alert=True)
            return

        elif data == "adm_broadcast":
            msg = bot.send_message(call.message.chat.id, "📢 <b>Отправьте сообщение для рассылки (текст, фото, видео или GIF):</b>")
            bot.register_next_step_handler(msg, execute_broadcast_media)
            return

        elif data == "adm_givemedia":
            msg = bot.send_message(call.message.chat.id, "📸 Введите ID пользователя для выдачи Медиа-Админки:")
            bot.register_next_step_handler(msg, set_media_admin)
            return

        elif data == "adm_giveadmin":
            msg = bot.send_message(call.message.chat.id, "🛡 Введите ID пользователя для выдачи Админки:")
            bot.register_next_step_handler(msg, set_full_admin)
            return

        elif data == "adm_removeadmin":
            msg = bot.send_message(call.message.chat.id, "❌ Введите ID пользователя для снятия прав:")
            bot.register_next_step_handler(msg, remove_admin)
            return

        elif data == "adm_addbal":
            msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и сумму баланса через пробел:")
            bot.register_next_step_handler(msg, give_balance)
            return

        elif data == "adm_reset_user_limit":
            msg = bot.send_message(call.message.chat.id, "⚡ Введите ID пользователя для сброса лимита:")
            bot.register_next_step_handler(msg, reset_user_limit)
            return

        elif data == "adm_resetall_limits":
            cursor.execute("UPDATE users SET comp_limit = 30")
            db.commit()
            bot.answer_callback_query(call.id, "✅ Лимиты всех пользователей сброшены!", show_alert=True)
            return

        elif data == "adm_addpromo":
            msg = bot.send_message(call.message.chat.id, "➕ Введите промокод, скидку (%) и лимит через пробел:")
            bot.register_next_step_handler(msg, save_promo)
            return

        elif data == "adm_listpromo":
            cursor.execute("SELECT code, discount, max_uses, used_count FROM promo")
            promos = cursor.fetchall()
            if not promos:
                bot.answer_callback_query(call.id, "Нет промокодов.", show_alert=True)
                return
            text = "📋 <b>Список промокодов:</b>\n\n"
            for p in promos:
                text += f"🎟 <code>{p[0]}</code> | {p[1]}% | {p[3]}/{p[2]}\n"
            bot.send_message(call.message.chat.id, text)
            return

        elif data == "adm_delpromo":
            msg = bot.send_message(call.message.chat.id, "🗑 Введите промокод для удаления:")
            bot.register_next_step_handler(msg, delete_promo)
            return

        elif data == "adm_clearpromo":
            cursor.execute("DELETE FROM promo")
            db.commit()
            bot.answer_callback_query(call.id, "❌ Все промокоды очищены!", show_alert=True)
            return

        elif data == "adm_userinfo":
            msg = bot.send_message(call.message.chat.id, "👤 Введите ID пользователя:")
            bot.register_next_step_handler(msg, get_user_info)
            return

        elif data == "adm_sendto":
            msg = bot.send_message(call.message.chat.id, "📨 Введите ID и текст сообщения через |:")
            bot.register_next_step_handler(msg, send_msg_to_user)
            return

        elif data == "adm_ban":
            msg = bot.send_message(call.message.chat.id, "🔨 Введите ID пользователя для бана:")
            bot.register_next_step_handler(msg, ban_user)
            return

        elif data == "adm_unban":
            msg = bot.send_message(call.message.chat.id, "🔓 Введите ID пользователя для разбана:")
            bot.register_next_step_handler(msg, unban_user)
            return

def set_media_admin(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_admin = 1, admin_role = 'media' WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Юзер <code>{uid}</code> стал Медиа-Админом!")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def set_full_admin(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_admin = 1, admin_role = 'admin' WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Юзер <code>{uid}</code> стал Админом!")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def remove_admin(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_admin = 0, admin_role = 'user' WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"❌ С юзера <code>{uid}</code> сняты админ-права.")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def give_balance(m: types.Message):
    try:
        parts = m.text.strip().split()
        uid, amt = int(parts[0]), int(parts[1])
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amt, uid))
        db.commit()
        bot.send_message(m.chat.id, f"💰 Выдано {amt} ₽ юзеру <code>{uid}</code>!")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка.")

def reset_user_limit(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET comp_limit = 30 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"⚡ Лимит компиляций для <code>{uid}</code> сброшен!")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def get_user_info(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("SELECT id, name, username, balance, comp_limit, is_banned, admin_role FROM users WHERE id = ?", (uid,))
        u = cursor.fetchone()
        if not u:
            bot.send_message(m.chat.id, "❌ Юзер не найден.")
            return
        info = (
            f"👤 <b>Инфо о юзере:</b>\n"
            f"🆔 ID: <code>{u[0]}</code>\n"
            f"👤 Имя: {u[1]}\n"
            f"🔗 Юзернейм: {u[2]}\n"
            f"💰 Баланс: {u[3]} ₽\n"
            f"🔨 Лимит: {u[4]}/30\n"
            f"🔨 Бан: {'Да' if u[5] else 'Нет'}\n"
            f"🔰 Роль: {u[6]}"
        )
        bot.send_message(m.chat.id, info)
    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID.")

def send_msg_to_user(m: types.Message):
    try:
        parts = m.text.split("|")
        uid, text = int(parts[0].strip()), parts[1].strip()
        bot.send_message(uid, f"💬 <b>Сообщение от администрации:</b>\n\n{text}")
        bot.send_message(m.chat.id, f"✅ Сообщение отправлено юзеру <code>{uid}</code>!")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка формата.")

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'animation', 'audio'])
def universal_user_message_handler(m: types.Message):
    uid = m.from_user.id
    if is_admin(uid):
        if m.reply_to_message:
            orig_text = m.reply_to_message.text or m.reply_to_message.caption or ""
            if "🆔 ID:" in orig_text or "🆔 ID клиента:" in orig_text:
                try:
                    target_id = int(orig_text.split("ID:")[1].split()[0].replace("<code>", "").replace("</code>", ""))
                    bot.copy_message(target_id, m.chat.id, m.message_id)
                    bot.send_message(m.chat.id, f"✅ Ответ отправлен пользователю <code>{target_id}</code>!")
                    return
                except Exception as e:
                    bot.send_message(m.chat.id, f"❌ Ошибка отправки: {e}")
        return

    try:
        username_str = f"@{m.from_user.username}" if m.from_user.username else "Отсутствует"
        header_caption = (
            f"💬 <b>СООБЩЕНИЕ В ТЕХ. ПОДДЕРЖКУ!</b>\n"
            f"{LINE}\n"
            f"👤 <b>Имя:</b> {m.from_user.full_name}\n"
            f"🔗 <b>Юзернейм:</b> {username_str}\n"
            f"🆔 <b>ID клиента:</b> <code>{uid}</code>\n"
            f"{LINE}\n"
            f"<i>Ответьте на это сообщение (Reply), чтобы отправить ответ!</i>"
        )
        
        if m.content_type == 'text':
            bot.send_message(PRIMARY_ADMIN_ID, f"{header_caption}\n\n<b>Текст:</b>\n{m.text}")
        else:
            bot.copy_message(PRIMARY_ADMIN_ID, m.chat.id, m.message_id, caption=header_caption)
            
        bot.send_message(m.chat.id, "✅ Ваше сообщение отправлено в техподдержку!")
    except Exception as e:
        logging.error(f"Support forward error: {e}")

def process_order_final(m: types.Message):
    uid = m.from_user.id
    item_title = user_order_step.get(uid, "Проект / Сборка")
    details = m.text.strip()
    
    u_data = get_user(uid, m.from_user.first_name)
    active_discount, active_promo_code = int(u_data[6] or 0), u_data[7]
    
    orig_price = 100
    if active_discount > 0:
        final_price = int(orig_price * (100 - active_discount) / 100)
        price_str = f"<s>{orig_price} ₽</s> 🔥 <b>{final_price} ₽</b> (-{active_discount}%)"
        cursor.execute("UPDATE users SET active_discount = 0, active_promo_code = '' WHERE id = ?", (uid,))
        db.commit()
    else:
        price_str = f"<b>{orig_price} ₽</b>"

    created_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO orders (user_id, item_title, price_str, details_text, status, created_at) VALUES (?, ?, ?, ?, '⏳ На рассмотрении', ?)", (uid, item_title, price_str, details, created_at))
    db.commit()
    oid = cursor.lastrowid

    bot.send_message(m.chat.id, f"✅ <b>Заказ #{oid} успешно оформлен!</b>\n🛍 {item_title}\n💰 К оплате: {price_str}\n\n💳 Оплата строго вперёд! Создатели свяжутся с вами.", reply_markup=menu(uid))
    
    try:
        admin_text = f"🛒 <b>НОВЫЙ ЗАКАЗ #{oid}!</b>\n👤 Юзер: {m.from_user.full_name} (<code>{uid}</code>)\n🛍 Товар: {item_title}\n💰 Цена: {price_str}\n\n<b>Детали:</b>\n<code>{details}</code>"
        bot.send_message(PRIMARY_ADMIN_ID, admin_text)
    except:
        pass

def execute_broadcast_media(m: types.Message):
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    success = 0
    for u in users:
        try:
            bot.copy_message(u[0], m.chat.id, m.message_id)
            success += 1
        except:
            pass
    bot.send_message(m.chat.id, f"✅ Рассылка завершена. Успешно отправлено: {success} пользователям.")

def save_promo(m: types.Message):
    try:
        parts = m.text.strip().split()
        code, disc, uses = parts[0], int(parts[1]), int(parts[2])
        cursor.execute("INSERT OR REPLACE INTO promo (code, discount, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, disc, uses))
        db.commit()
        bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> создан!")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка формата.")

def delete_promo(m: types.Message):
    code = m.text.strip().upper()
    cursor.execute("DELETE FROM promo WHERE code = ?", (code,))
    db.commit()
    bot.send_message(m.chat.id, f"✅ Промокод <code>{code}</code> удален.")

def ban_user(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔨 Пользователь <code>{uid}</code> забанен.")
    except:
        bot.send_message(m.chat.id, "❌ Неверный ID.")

def unban_user(m: types.Message):
    try:
        uid = int(m.text.strip())
        cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (uid,))
        db.commit()
        bot.send_message(m.chat.id, f"🔓 Пользователь <code>{uid}</code> разблокирован.")
    except:
        bot.send_message(m.chat.id, "❌ Неверный ID.")

if __name__ == "__main__":
    print("BLACK STUDIO SHOP запущен!")
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    try:
        bot.remove_webhook()
    except Exception:
        pass

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)
