import logging
import asyncio
import threading
import os

from flask import Flask
from telegram import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllChatAdministrators,
)
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN
from handlers.welcome import welcome
from handlers.menu import start_command, button_handler
from services.telegram import (
    anti_spam_handler,
    cmd_delete,
    cmd_kick,
    cmd_chat,
    cmd_ban,
    cmd_purge_user,
    cmd_purge_all,
    clean_service_messages,
)

# ==========================
# Flask Web Server cho Render
# ==========================

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is running!", 200

@web.route("/health")
def health():
    return {"status": "ok"}, 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)


# ==========================
# Telegram Bot
# ==========================

async def post_init(application: Application):
    bot = application.bot

    # Menu người dùng
    await bot.set_my_commands(
        [
            BotCommand("start", "Menu hỗ trợ"),
        ],
        scope=BotCommandScopeDefault(),
    )

    # Menu Admin
    await bot.set_my_commands(
        [
            BotCommand("start", "Menu hỗ trợ"),
            BotCommand("delete", "Xóa tin nhắn"),
            BotCommand("kick", "Kick thành viên"),
            BotCommand("chat", "Khóa chat 2h"),
            BotCommand("ban", "Ban vĩnh viễn"),
            BotCommand("purge_user", "Xóa sạch tin nhắn User"),
            BotCommand("purge_all", "Dọn dẹp nhóm"),
        ],
        scope=BotCommandScopeAllChatAdministrators(),
    )


async def main():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # Khởi động Web Server
    threading.Thread(target=run_web, daemon=True).start()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ==========================
    # HANDLERS
    # ==========================

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS
            | filters.StatusUpdate.LEFT_CHAT_MEMBER,
            clean_service_messages,
        )
    )

    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("chat", cmd_chat))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("purge_user", cmd_purge_user))
    app.add_handler(CommandHandler("purge_all", cmd_purge_all))

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            anti_spam_handler,
        )
    )

    print("========================================")
    print("Bot Started! (Thành Quý Tech System)")
    print("========================================")

    async with app:
        await app.start()
        await app.updater.start_polling()

        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
