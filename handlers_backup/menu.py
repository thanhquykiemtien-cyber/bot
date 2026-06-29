from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import ADMIN_IDS

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🪪 Xem ID của tôi", callback_data="show_id")],
        [InlineKeyboardButton("🌐 Mua Key Tool", callback_data="show_keytool")],
        [InlineKeyboardButton("📚 Hướng dẫn thêm Acc", callback_data="hd_acc")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_acc_menu():
    keyboard = [
        [InlineKeyboardButton("Golike", callback_data="sub_golike"),
         InlineKeyboardButton("TraoDoiSub", callback_data="sub_tds")],
        [InlineKeyboardButton("TuongTacCheo", callback_data="sub_ttc")],
        [InlineKeyboardButton("⇦ Quay lại", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    if chat_type == 'private' and user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "**Bot chỉ hoạt động trong nhóm.**\n"
            "Vui lòng tham gia nhóm của chúng tôi để sử dụng các tính năng hỗ trợ.\n"
            "👉 https://t.me/thanhquytechoffice"
        )
        return
    text = "<blockquote>Bạn cần hỗ trợ gì hôm nay?</blockquote>"
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=get_main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_id":
        user_id = query.from_user.id
        await query.message.reply_text(f"🪪 ID của bạn là: <code>{user_id}</code>", parse_mode=ParseMode.HTML)
    
    elif query.data == "show_keytool":
        await query.message.reply_text("🔑 Để mua Key sử dụng Tool, vui lòng truy cập:\nhttps://thanhquytech.com/buy-key")
    
    elif query.data == "hd_acc":
        await query.edit_message_text("📖 Vui lòng chọn nền tảng để xem hướng dẫn:", reply_markup=get_acc_menu())
    
    elif query.data == "back_main":
        await query.edit_message_text("<blockquote>Bạn cần hỗ trợ gì hôm nay?</blockquote>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
    
    elif query.data.startswith("sub_"):
        platform = query.data.split("_")[1]
        if platform == "golike":
            text = "📖 Hướng dẫn thêm tài khoản vào <b>GoLike</b>:"
            keyboard = [
                [InlineKeyboardButton("📱 Facebook Golike", url="https://thanhquytech.com/fb-golike")],
                [InlineKeyboardButton("⇦ Quay lại", callback_data="hd_acc")]
            ]
        elif platform == "tds":
            text = "📖 Hướng dẫn thêm tài khoản vào <b>Trao Đổi Sub</b>:"
            keyboard = [
                [InlineKeyboardButton("📱 FB Tds", url="https://thanhquytech.com/fb-tds")],
                [InlineKeyboardButton("🎵 TikTok Tds", url="https://thanhquytech.com/tt-tds")],
                [InlineKeyboardButton("⇦ Quay lại", callback_data="hd_acc")]
            ]
        elif platform == "ttc":
            text = "📖 Hướng dẫn thêm tài khoản vào <b>Tương Tác Chéo</b>:"
            keyboard = [
                [InlineKeyboardButton("📱 FB Ttc", url="https://thanhquytech.com/fb-ttc")],
                [InlineKeyboardButton("⇦ Quay lại", callback_data="hd_acc")]
            ]
        else:
            return
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))