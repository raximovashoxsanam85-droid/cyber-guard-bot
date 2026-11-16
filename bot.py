import asyncio
import logging
import random
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

TOKEN = "9172313511:AAESF1AxL_bZCeGg8ta_PZNBVJrviNlGZuE"

# O'z Telegram ID raqamingizni yozing
ADMIN_ID = 5794080797

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_states = {}
user_quiz = {}
registered_users = {}

QUIZ_QUESTIONS = [
    {
        "question": "1. Internetda o'zingiz tanimagan shaxslardan kelgan shubhali havolaga duch kelsangiz nima qilish kerak?",
        "options": {"A": "Darhol ustiga bosib kirish kerak", "B": "Havolani ochmasdan o'chirib tashlash kerak", "C": "Do'stlarga ulashish kerak"},
        "answer": "B",
        "explanation": "Shubhali havolalar orqali firibgarlar shaxsiy ma'lumotlaringizni o'g'irlashi mumkin."
    },
    {
        "question": "2. Telegram yoki boshqa ijtimoiy tarmoqlarda akkauntingizni himoya qilish uchun nima qilish shart?",
        "options": {"A": "Har kuni parolni o'zgartirish", "B": "Ikki bosqichli autentifikatsiyani (2FA) yoqib qo'yish", "C": "Parolni barchaga ulashish"},
        "answer": "B",
        "explanation": "Ikki bosqichli autentifikatsiya akkauntingizni xavfsiz saqlaydi."
    },
    {
        "question": "3. Wi-Fi tarmog'iga ulanishda qaysi biri xavfsizroq hisoblanadi?",
        "options": {"A": "Paroli yo'q ochiq Wi-Fi", "B": "Shifrlangan va parolli shaxsiy Wi-Fi", "C": "Ko'pchilik foydalanadigan bepul tarmoq"},
        "answer": "B",
        "explanation": "Ochiq tarmoqlarda trafigingizni boshqalar kuzatishi mumkin."
    },
    {
        "question": "4. Fishing (Phishing) hujumi nima maqsadda amalga oshiriladi?",
        "options": {"A": "Kompyuter tezligini oshirish", "B": "Parol va bank karta ma'lumotlarini o'g'irlash", "C": "Internet tezligini tekshirish"},
        "answer": "B",
        "explanation": "Fishing — soxta sahifalar orqali ma'lumotlarni aldab olish usuli."
    },
    {
        "question": "5. Kuchli parol qanday bo'lishi kerak?",
        "options": {"A": "Tug'ilgan yil va ism", "B": "Faqat raqamlar (123456)", "C": "Harflar, raqamlar va maxsus belgilar (8 tadan ko'p)"},
        "answer": "C",
        "explanation": "Murakkab parollarni maxsus dasturlar ham qiyinchilik bilan topadi."
    },
    {
        "question": "6. E-pochtangizga noma'lum shaxsdan yirik miqdordagi pul yutib olganingiz haqida xat kelsa?",
        "options": {"A": "Havolaga kirib ma'lumot kiritish", "B": "Xatni o'chirib tashlash va spamga solish", "C": "Pasport ma'lumotlarini yuborish"},
        "answer": "B",
        "explanation": "Bunday xabarlar har doim firibgarlarga tegishli bo'ladi."
    },
    {
        "question": "7. Kompyuterga antivirus o'rnatish nima uchun kerak?",
        "options": {"A": "O'yinlar tez ishlashi uchun", "B": "Zararli va virusli dasturlardan himoyalanish uchun", "C": "Internetni tezlashtirish uchun"},
        "answer": "B",
        "explanation": "Antivirus xavfli fayllarni o'z vaqtida aniqlab bloklaydi."
    },
    {
        "question": "8. Jamoat joyida telefon yoki noutbukni qarovsiz qoldirganda?",
        "options": {"A": "Ochiq holda tashlab ketish", "B": "Ekranni bloklab, o'zingiz bilan olib yurish", "C": "Begonadan qarab turishni so'rash"},
        "answer": "B",
        "explanation": "Qarovsiz qolgan qurilmadan ma'lumot o'g'irlash oson."
    },
    {
        "question": "9. Ilovalarni qayerdan yuklab olish xavfsizroq?",
        "options": {"A": "Noma'lum saytlardan apk fayl ko'rinishida", "B": "Faqat rasmiy do'konlardan (Google Play / App Store)", "C": "Telegram kanallardagi noma'lum botlardan"},
        "answer": "B",
        "explanation": "Rasmiy do'konlar ilovalarni xavfsizlik tekshiruvidan o'tkazadi."
    },
    {
        "question": "10. Bank kartangizning CVV kodi yoki SMS kodini kimga aytish mumkin?",
        "options": {"A": "Bank xodimiga (agar so'rasa)", "B": "Hech kimga, hatto bank xodimiga ham", "C": "Yaqin do'stlarga"},
        "answer": "B",
        "explanation": "Haqiqiy bank xodimi maxfiy kodlarni hech qachon so'ramaydi."
    }
]

def get_phone_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📞 Telefon raqamni ulashish", request_contact=True)
    return builder.as_markup(resize_keyboard=True)

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🛡 Xavfsizlik maslahatlari")
    builder.button(text="🔑 Parol yaratish")
    builder.button(text="🔍 Parolni tekshirish")
    builder.button(text="🔗 Havolani tekshirish")
    builder.button(text="❓ Viktorina o'ynash")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    if user_id not in registered_users:
        await message.answer(
            f"Salom, {first_name}! 🛡\n\n"
            "Botdan to'liq foydalanish uchun iltimos, pastdagi **📞 Telefon raqamni ulashish** tugmasini bosing:",
            reply_markup=get_phone_keyboard()
        )
        return

    await show_main_menu(message)

async def show_main_menu(message: types.Message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    user_quiz.pop(user_id, None)
    
    welcome_text = "Men **CyberGuard Assistant** — shaxsiy kiberxavfsizlik yordamchingizman.\nQuyidagi bo'limni tanlang:"
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@dp.message(lambda message: message.contact is not None)
async def contact_handler(message: types.Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    first_name = message.from_user.first_name
    username = message.from_user.username or "Kiritilmagan"
    
    registered_users[user_id] = {"name": first_name, "phone": phone, "username": username}
    
    admin_notification = (
        f"🚨 **Yangi foydalanuvchi botga kirdi!**\n\n"
        f"👤 **Ismi (User):** {first_name}\n"
        f"🔗 **Username:** @{username}\n"
        f"📞 **Telefon raqami:** +{phone}\n"
        f"🆔 **ID raqami:** `{user_id}`"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_notification, parse_mode="Markdown")
    except Exception as e:
        print(f"Adminga xabar yuborishda xatolik: {e}")

    await message.answer("Rahmat! Ma'lumotlaringiz muvaffaqiyatli qabul qilindi. ✅", reply_markup=types.ReplyKeyboardRemove())
    await show_main_menu(message)

@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in registered_users:
        await message.answer("Iltimos, botdan foydalanish uchun avval **📞 Telefon raqamni ulashish** tugmasini bosing.", reply_markup=get_phone_keyboard())
        return

    text = message.text.strip()

    if text == "🏠 Asosiy menyu":
        await show_main_menu(message)
        return

    if text == "🛡 Xavfsizlik maslahatlari":
        user_states.pop(user_id, None)
        tips_text = (
            "🔐 **Kiberxavfsizlik bo'yicha oltin qoidalar:**\n\n"
            "1️⃣ **2FA yoqing:** Telegram va ijtimoiy tarmoqlarda ikki bosqichli himoyani faollashtiring.\n"
            "2️⃣ **Turli parollar:** Har bir sayt uchun alohida parol ishlating.\n"
            "3️⃣ **SMS kodlar:** \"Yutuq chiqdi\" deb kod so'raganlarga aslo bermang.\n"
            "4️⃣ **Havolalar:** Noma'lum havolalarga kirmang.\n"
            "5️⃣ **Rasmiy ilovalar:** Dasturlarni faqat Google Play / App Store'dan oling."
        )
        await message.answer(tips_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

    elif text == "🔑 Parol yaratish":
        user_states.pop(user_id, None)
        words = ["Cyber", "Guard", "Shield", "Secure", "Matrix", "Portal", "Access", "Token", "Firewall", "Lock"]
        symbols = ["!", "@", "#", "$", "*"]
        w1 = random.choice(words)
        w2 = random.choice(words)
        num = random.randint(10, 99)
        sym = random.choice(symbols)
        password = f"{w1}_{w2}{num}{sym}"
        
        await message.answer(
            f"🔑 **Siz uchun chiroyli va xavfsiz parol yaratildi:**\n\n"
            f"`{password}`\n\n"
            f"<i>Nusxalab olib, xavfsiz joyda saqlang!</i>",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )

    elif text == "🔍 Parolni tekshirish":
        user_states[user_id] = "checking_password"
        await message.answer(
            "🔍 Tekshirmoqchi bo'lgan parolingizni yozib yuboring.\n"
            "<i>(Bot parolingizni hech qayerga saqlamaydi)</i>",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )

    elif text == "🔗 Havolani tekshirish":
        user_states[user_id] = "checking_url"
        await message.answer(
            "🔗 Tekshirmoqchi bo'lgan havolani (linkni) yuboring. Men uning xavflilik darajasini tekshiraman:",
            reply_markup=get_main_keyboard()
        )

    elif text == "❓ Viktorina o'ynash":
        user_states[user_id] = "in_quiz"
        user_quiz[user_id] = {"index": 0, "score": 0}
        await send_inline_quiz_question(message, user_id)

    elif user_states.get(user_id) == "checking_password":
        pwd = text
        issues = []
        if len(pwd) < 8:
            issues.append("❌ Kamida 8 ta belgi bo'lishi kerak.")
        if not any(c.isupper() for c in pwd):
            issues.append("⚠️ Katta harf (A-Z) qo'shing.")
        if not any(c.islower() for c in pwd):
            issues.append("⚠️ Kichik harf (a-z) qo'shing.")
        if not any(c.isdigit() for c in pwd):
            issues.append("⚠️ Raqam (0-9) qo'shing.")
        if not