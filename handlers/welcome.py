from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import WELCOME_TOPIC_ID

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    keyboard = [
        [InlineKeyboardButton("📢 Thông báo", url="https://t.me/thanhquytechoffice/6"), 
         InlineKeyboardButton("💬 Chat", url="https://t.me/thanhquytechoffice/1")],
        [InlineKeyboardButton("📚 Hướng dẫn", url="https://t.me/thanhquytechoffice/5"), 
         InlineKeyboardButton("📥 Tải tool", url="https://t.me/thanhquytechoffice/4")],
        [InlineKeyboardButton("⚠️ Báo lỗi", url="https://t.me/thanhquytechoffice/3"), 
         InlineKeyboardButton("💬 Hỗ trợ", url="https://t.me/thanhquytech")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    for user in update.message.new_chat_members:
        if user.is_bot: continue
        mention = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
        text = (
            f"<blockquote>"
            f"🎉 <b>Chào mừng {mention}</b>\n\n"
            f"Chào mừng bạn đến với <b>Thành Quý Tech</b> ❤️\n\n"
            f"📢 <i>Vui lòng chọn chức năng bên dưới để bắt đầu:</i>"
            f"</blockquote>"
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            message_thread_id=WELCOME_TOPIC_ID, 
            text=text, 
            parse_mode=ParseMode.HTML, 
            reply_markup=reply_markup
        )