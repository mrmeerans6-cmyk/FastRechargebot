import os
import io
import qrcode

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
UPI_ID = os.environ.get("UPI_ID", "yourupi@upi")

DISCOUNT_PERCENT = 60

# =========================
# PLANS
# =========================

PLANS = {
    "Jio": [
        {
            "price": 199,
            "validity": "18 Days",
            "data": "1.5 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
        {
            "price": 299,
            "validity": "28 Days",
            "data": "1.5 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
        {
            "price": 349,
            "validity": "28 Days",
            "data": "2 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
    ],

    "Airtel": [
        {
            "price": 199,
            "validity": "28 Days",
            "data": "2 GB Total",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
        {
            "price": 299,
            "validity": "28 Days",
            "data": "1.5 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
        {
            "price": 349,
            "validity": "28 Days",
            "data": "2 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
    ],

    "Vi": [
        {
            "price": 199,
            "validity": "18 Days",
            "data": "1 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
        {
            "price": 299,
            "validity": "28 Days",
            "data": "1.5 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
        {
            "price": 349,
            "validity": "28 Days",
            "data": "2 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
    ],

    "BSNL": [
        {
            "price": 199,
            "validity": "30 Days",
            "data": "2 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
        {
            "price": 299,
            "validity": "30 Days",
            "data": "3 GB/Day",
            "calls": "Unlimited Calls",
            "sms": "100 SMS/Day",
        },
    ],
}


def offer_price(price):
    return round(price * 0.40, 2)


# =========================
# START MENU
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = [
        [
            InlineKeyboardButton("📱 Jio", callback_data="operator:Jio"),
            InlineKeyboardButton("📱 Airtel", callback_data="operator:Airtel"),
        ],
        [
            InlineKeyboardButton("📱 Vi", callback_data="operator:Vi"),
            InlineKeyboardButton("📱 BSNL", callback_data="operator:BSNL"),
        ],
    ]

    await update.message.reply_text(
        "🔥 *WELCOME TO FASTRECHARGE* 🔥\n\n"
        "Get selected recharge plans with *60% OFF*.\n\n"
        "📱 Select your operator:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# =========================
# SHOW PLANS
# =========================

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    operator = query.data.split(":")[1]

    buttons = []

    for i, plan in enumerate(PLANS[operator]):

        original = plan["price"]
        offer = offer_price(original)

        buttons.append([
            InlineKeyboardButton(
                f"₹{original} → ₹{offer} 🔥",
                callback_data=f"plan:{operator}:{i}",
            )
        ])

    buttons.append([
        InlineKeyboardButton("⬅️ Back", callback_data="back")
    ])

    await query.edit_message_text(
        f"📱 *{operator} RECHARGE PLANS*\n\n"
        f"🔥 *60% OFF*\n\n"
        f"Select your plan:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# =========================
# PLAN DETAILS
# =========================

async def plan_details(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    _, operator, index = query.data.split(":")

    index = int(index)
    plan = PLANS[operator][index]

    original = plan["price"]
    offer = offer_price(original)

    context.user_data["plan"] = {
        "operator": operator,
        "index": index,
    }

    text = (
        f"📋 *{operator} PLAN DETAILS*\n\n"
        f"💰 Original Price: ₹{original}\n"
        f"🔥 60% OFF Price: *₹{offer}*\n\n"
        f"📅 Validity: {plan['validity']}\n"
        f"📶 Data: {plan['data']}\n"
        f"📞 Calls: {plan['calls']}\n"
        f"💬 SMS: {plan['sms']}\n\n"
        f"👇 Click below to continue."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📲 Recharge Now",
                callback_data="recharge",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=f"operator:{operator}",
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# ASK MOBILE
# =========================

async def recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if "plan" not in context.user_data:
        await query.message.reply_text(
            "❌ Session expired. Please use /start again."
        )
        return

    context.user_data["waiting_mobile"] = True

    await query.message.reply_text(
        "📱 *Enter your 10-digit mobile number*\n\n"
        "Example: `9876543210`",
        parse_mode="Markdown",
    )


# =========================
# MOBILE NUMBER
# =========================

async def mobile_number(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("waiting_mobile"):
        return

    mobile = update.message.text.strip()

    if not mobile.isdigit() or len(mobile) != 10:
        await update.message.reply_text(
            "❌ Invalid number.\n\n"
            "Please enter a valid 10-digit mobile number."
        )
        return

    if mobile[0] not in "6789":
        await update.message.reply_text(
            "❌ Please enter a valid Indian mobile number."
        )
        return

    context.user_data["mobile"] = mobile
    context.user_data["waiting_mobile"] = False

    selected = context.user_data["plan"]

    operator = selected["operator"]
    index = selected["index"]

    plan = PLANS[operator][index]

    original = plan["price"]
    amount = offer_price(original)

    # U
