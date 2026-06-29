import logging
import asyncio
from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeAllChatAdministrators
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers.welcome import welcome
from handlers.menu import start_command, button_handler
from services.telegram import anti_spam_handler, cmd_delete, cmd_kick, cmd_chat, cmd_ban, cmd_purge_user, cmd_purge_all, clean_service_messages

async def post_init(application: Application):
    bot = application.bot
    
    # 1. Menu cho tất cả mọi người (Hiện ở mọi nơi)
    await bot.set_my_commands([
        BotCommand("start", "Menu hỗ trợ"),
    ], scope=BotCommandScopeDefault())

    # 2. Menu lệnh Admin (Chỉ Admin nhóm mới thấy thêm các lệnh này)
    await bot.set_my_commands([
        BotCommand("start", "Menu hỗ trợ"),
        BotCommand("delete", "Xóa tin nhắn"),
        BotCommand("kick", "Kick thành viên"),
        BotCommand("chat", "Khóa chat 2h"),
        BotCommand("ban", "Ban vĩnh viễn"),
        BotCommand("purge_user", "Xóa sạch tin nhắn User"),
        BotCommand("purge_all", "Dọn dẹp nhóm"),
    ], scope=BotCommandScopeAllChatAdministrators())

async def main():
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Sửa đoạn đăng ký handler trong main.py thành:
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS | 
        filters.StatusUpdate.LEFT_CHAT_MEMBER, 
        clean_service_messages
    ))
    
    # --- HANDLERS ---
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # Lệnh Admin
    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("chat", cmd_chat))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("purge_user", cmd_purge_user))
    app.add_handler(CommandHandler("purge_all", cmd_purge_all))

    # Anti-Spam (Luôn đặt cuối cùng)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, anti_spam_handler))

    print("Bot Started! (Thành Quý Tech System)")
    
    # Khởi chạy bot bất đồng bộ thay thế cho app.run_polling() để sửa lỗi trên Render
    async with app:
        await app.updater.start_polling()
        await app.start()
        
        # Giữ cho tiến trình luôn chạy ngầm liên tục
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    # Sử dụng asyncio để kích hoạt hàm main
    asyncio.run(main())