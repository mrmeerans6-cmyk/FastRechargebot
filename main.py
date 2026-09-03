import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("8818925720:AAF929jv8V_q6HMn8nr1OZxSR9nzBuNYfCs")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
UPI_ID = os.getenv("okcclipol@airtel")

DISCOUNT = 0.40  # User pays 40% = 60% OFF

PLANS = {
    "jio": [
        ("₹239", "28 Days • 1.5GB/day • Unlimited Calls • 100 SMS/day", 239),
        ("₹299", "28 Days • 1.5GB/day • Unlimited Calls • 100 SMS/day", 299),
        ("₹349", "28 Days • 2GB/day • Unlimited Calls • 100 SMS/day", 349),
    ],
    "airtel": [
        ("₹199", "28 Days • 2GB total • Unlimited Calls • 100 SMS/day", 199),
        ("₹299", "28 Days • 1.5GB/day • Unlimited Calls • 100 SMS/day", 299),
        ("₹349", "28 Days • 2GB/day • Unlimited Calls • 100 SMS/day", 349),
    ],
    "vi": [
        ("₹199", "28 Days • 2GB total • Unlimited Calls", 199),
        ("₹299", "28 Days • 1.5GB/day • Unlimited Calls • 100 SMS/day", 299),
        ("₹349", "28 Days • 1.5GB/day • Unlimited Calls • 100 SMS/day", 349),
    ],
    "bsnl": [
        ("₹199", "30 Days • Data + Calls", 199),
        ("₹299", "30 Days • Daily Data + Unlimited Calls", 299),
        ("₹397", "150 Days • Voice + Data Benefits", 397),
    ],
}


def final_price(price):
    return round(price * DISCOUNT)


def operator_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📱 Jio", callback_data="op_jio"),
            InlineKeyboardButton("📱 Airtel", callback_data="op_airtel"),
        ],
        [
            InlineKeyboardButton("📱 Vi", callback_data="op_vi"),
            InlineKeyboardButton("📱 BSNL", callback_data="op_bsnl"),
        ],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 *WELCOME TO FASTRECHARGE* 🔥\n\n"
        "Get mobile recharge plans with *60% OFF*.\n\n"
        "📱 Select your operator below:"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=operator_keyboard(),
    )


async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("op_"):
        operator = data.replace("op_", "")

        buttons = []

        for index, plan in enumerate(PLANS[operator]):
            name, details, price = plan
            discounted = final_price(price)

            buttons.append([
                InlineKeyboardButton(
                    f"{name} → ₹{discounted} 🔥",
                    callback_data=f"plan_{operator}_{index}",
                )
            ])

        buttons.append([
            InlineKeyboardButton("⬅️ Back", callback_data="back")
        ])

        await query.edit_message_text(
            f"📱 *{operator.upper()} RECHARGE PLANS*\n\n"
            f"🔥 *60% OFF*\n\n"
            f"Select a plan:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data == "back":
        await query.edit_message_text(
            "🔥 *FASTRECHARGE*\n\nSelect your operator:",
            parse_mode="Markdown",
            reply_markup=operator_keyboard(),
        )

    elif data.startswith("plan_"):
        _, operator, index = data.split("_")
        index = int(index)

        name, details, price = PLANS[operator][index]
        discounted = final_price(price)

        context.user_data["selected_plan"] = {
            "operator": operator,
            "name": name,
            "details": details,
            "price": price,
            "discounted": discounted,
        }

        await query.message.reply_text(
            f"📋 *PLAN DETAILS*\n\n"
            f"📱 Operator: *{operator.upper()}*\n"
            f"📦 Plan: *{name}*\n"
            f"📝 {details}\n\n"
            f"💰 Original Price: ₹{price}\n"
            f"🔥 60% OFF Price: *₹{discounted}*\n\n"
            f"📲 Please send your *10-digit mobile number*.",
            parse_mode="Markdown",
        )

    elif data == "paid":
        order = context.user_data.get("order")

        if not order:
            await query.message.reply_text(
                "❌ Order session expired. Please select the plan again."
            )
            return

        await send_admin_order(context, order)

        await query.message.reply_text(
            f"✅ *Payment request submitted!*\n\n"
            f"🧾 Order ID: *{order['id']}*\n"
            f"📱 Mobile: *{order['mobile']}*\n\n"
            f"⏳ Admin will verify your payment.\n"
            f"You will receive an approval/decline notification.",
            parse_mode="Markdown",
        )

    elif data.startswith("approve_") or data.startswith("decline_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("⛔ Admin only", show_alert=True)
            return

        action, order_id, user_id = data.split("_")
        user_id = int(user_id)

        if action == "approve":
            await context.bot.send_message(
                user_id,
                f"🎉 *PAYMENT APPROVED* ✅\n\n"
                f"🧾 Order ID: *{order_id}*\n\n"
                f"Your payment has been approved by admin.",
                parse_mode="Markdown",
            )

            await query.edit_message_text(
                f"✅ Order *{order_id}* APPROVED.",
                parse_mode="Markdown",
            )

        else:
            await context.bot.send_message(
                user_id,
                f"❌ *PAYMENT DECLINED*\n\n"
                f"🧾 Order ID: *{order_id}*\n\n"
                f"Your payment request was declined by admin.",
                parse_mode="Markdown",
            )

            await query.edit_message_text(
                f"❌ Order *{order_id}* DECLINED.",
                parse_mode="Markdown",
            )


async def mobile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mobile = update.message.text.strip().replace(" ", "")

    if not mobile.isdigit() or len(mobile) != 10 or mobile[0] not in "6789":
        await update.message.reply_text(
            "❌ Please send a valid 10-digit Indian mobile number."
        )
        return

    plan = context.user_data.get("selected_plan")

    if not plan:
        await update.message.reply_text(
            "Please select a plan first using /start."
        )
        return

    import time
    order_id = "FR" + str(int(time.time()))[-8:]

    order = {
        "id": order_id,
        "user_id": update.effective_user.id,
        "user_name": update.effective_user.first_name or "User",
        "mobile": mobile,
        **plan,
    }

    context.user_data["order"] = order

    amount = plan["discounted"]

    upi_link = (
        f"upi://pay?pa={UPI_ID}"
        f"&pn=FastRecharge"
        f"&am={amount}"
        f"&cu=INR"
        f"&tn={order_id}"
    )

    import urllib.parse
    qr_url = (
        "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data="
        + urllib.parse.quote(upi_link)
    )

    await update.message.reply_photo(
        photo=qr_url,
        caption=(
            f"💳 *PAYMENT DETAILS*\n\n"
            f"🧾 Order ID: *{order_id}*\n"
            f"📱 Mobile: *{mobile}*\n"
            f"📦 Plan: *{plan['name']}*\n"
            f"📡 Operator: *{plan['operator'].upper()}*\n\n"
            f"💰 Amount: *₹{amount}*\n\n"
            f"UPI ID: `{UPI_ID}`\n\n"
            f"1️⃣ Pay the exact amount\n"
            f"2️⃣ Tap *I HAVE PAID*\n"
            f"3️⃣ Admin will verify your payment"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 I HAVE PAID", callback_data="paid")]
        ]),
    )


async def send_admin_order(context, order):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ APPROVE",
                callback_data=f"approve_{order['id']}_{order['user_id']}",
            ),
            InlineKeyboardButton(
                "❌ DECLINE",
                callback_data=f"decline_{order['id']}_{order['user_id']}",
            ),
        ]
    ])

    await context.bot.send_message(
        ADMIN_ID,
        f"🔔 *NEW RECHARGE ORDER*\n\n"
        f"🧾 Order ID: *{order['id']}*\n"
        f"👤 User: {order['user_name']}\n"
        f"🆔 Telegram ID: `{order['user_id']}`\n"
        f"📱 Mobile: *{order['mobile']}*\n"
        f"📡 Operator: *{order['operator'].upper()}*\n"
        f"📦 Plan: *{order['name']}*\n"
        f"📝 {order['details']}\n\n"
        f"💰 Amount: *₹{order['discounted']}*\n\n"
        f"Choose action:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("plans", plans))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, mobile_handler)
    )

    print("FastRecharge Bot Started...")
    application.run_polling()


if __name__ == "__main__":
    main()
