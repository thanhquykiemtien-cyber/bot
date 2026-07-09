import time
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import ChatPermissions, Update
from telegram.ext import ContextTypes, filters
from config import ADMIN_IDS
from telegram.error import BadRequest

# --- CẤU HÌNH NGƯỠNG CHỐNG SPAM ---
SPAM_INTERVAL = 5          # Khoảng thời gian (giây) giữa các tin nhắn để tính là spam liên tục
SPAM_THRESHOLD = 3         # Gửi liên tiếp 3 tin nhắn trong khoảng thời gian trên sẽ bị phạt
RESET_VIOLATION_TIME = 86400  # 24 giờ (tính bằng giây) để reset mức độ cảnh báo về 0

# Cấu hình DB lưu trữ riêng biệt theo từng loại media để tránh chặn nhầm xen kẽ
# violation_db[chat_id][user_id] = {
#     "violations": 0,
#     "last_violation_time": 0,
#     "media_tracks": { "photo": [], "sticker": [], "url": [], "video": [] }
# }
violation_db = defaultdict(lambda: defaultdict(lambda: {
    "violations": 0, 
    "last_violation_time": 0, 
    "media_tracks": defaultdict(list)
}))

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        return True
    try:
        chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return chat_member.status in ['administrator', 'creator']
    except Exception:
        return False

async def punish_user(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str):
    user = update.effective_user
    chat_id = update.effective_chat.id
    data = violation_db[chat_id][user.id]
    current_time = time.time()
    
    # 1. KIỂM TRA RESET SAU 24H: Nếu khoảng cách từ lần bị phạt trước tới giờ > 24h -> Reset như mới
    if data["last_violation_time"] > 0 and (current_time - data["last_violation_time"] > RESET_VIOLATION_TIME):
        data["violations"] = 0

    data["violations"] += 1
    data["last_violation_time"] = current_time # Cập nhật mốc thời gian bị phạt gần nhất
    
    # 2. TIẾN HÀNH XỬ PHẠT THEO CẤP ĐỘ
    if data["violations"] == 1:
        await update.message.reply_text(f"⚠️ {user.first_name} vui lòng không gửi {reason} liên tục (Cảnh báo 1/3).")
    elif data["violations"] == 2:
        until = datetime.now() + timedelta(hours=2)
        try:
            await context.bot.restrict_chat_member(chat_id, user.id, ChatPermissions(can_send_messages=False), until_date=until)
            await update.message.reply_text(f"⚠️ {user.first_name} đã bị khóa chat 2h vì cố tình {reason} liên tục (Cảnh báo 2/3).")
        except BadRequest:
            pass
    elif data["violations"] >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            await update.message.reply_text(f"🚫 {user.first_name} đã bị BAN vĩnh viễn khỏi nhóm vì spam {reason} quá nhiều lần.")
        except BadRequest:
            pass

async def anti_spam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await is_admin(update, context): return
    
    msg = update.message
    media_type = None
    reason = ""

    # Phân loại chính xác loại tin nhắn đang gửi
    if msg.entities and any(e.type in ['url', 'text_link'] for e in msg.entities):
        media_type = "url"
        reason = "Liên kết (Link)"
    elif msg.photo:
        media_type = "photo"
        reason = "Hình ảnh"
    elif msg.video or msg.animation:
        media_type = "video"
        reason = "Video/GIF"
    elif msg.sticker:
        media_type = "sticker"
        reason = "Sticker"
        
    # Nếu tin nhắn thuộc các loại cần check spam
    if media_type:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        current_time = time.time()
        
        user_data = violation_db[chat_id][user_id]
        timestamps = user_data["media_tracks"][media_type]
        
        # Thêm thời gian của tin nhắn hiện tại vào bộ đếm của loại media đó
        timestamps.append(current_time)
        
        # LỌC THỜI GIAN: Chỉ giữ lại những tin nhắn gửi trong vòng 5 giây trở lại đây
        # Nếu gửi cách nhau 2-3 phút, các timestamp cũ sẽ bị xóa sạch khỏi list này!
        user_data["media_tracks"][media_type] = [t for t in timestamps if current_time - t <= SPAM_INTERVAL]
        
        # Nếu trong vòng 5 giây mà loại media này có từ 3 tin nhắn trở lên -> Phạt!
        if len(user_data["media_tracks"][media_type]) >= SPAM_THRESHOLD:
            user_data["media_tracks"][media_type].clear() # Phạt xong xóa lịch sử đếm spam ngay
            await punish_user(update, context, reason)

# --- CÁC COMMAND QUẢN TRỊ VIÊN GIỮ NGUYÊN ---
async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except BadRequest: pass

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        except BadRequest: pass

async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        until = datetime.now() + timedelta(hours=2)
        try:
            await context.bot.restrict_chat_member(update.effective_chat.id, user_id, ChatPermissions(can_send_messages=False), until_date=until)
            await update.message.reply_text("Đã khóa chat thành viên trong 2h.")
        except BadRequest: pass

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user.id)
            await update.message.reply_text(f"🚫 Đã BAN vĩnh viễn {user.first_name}.")
        except BadRequest: pass
    else:
        await update.message.reply_text("Vui lòng reply tin nhắn của người cần ban.")

async def cmd_purge_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message:
        await update.message.reply_text("Vui lòng reply tin nhắn của người cần xóa lịch sử chat.")
        return
    target_user = update.message.reply_to_message.from_user
    await update.message.reply_text(f"Đang xóa tin nhắn của {target_user.first_name}...")

async def cmd_purge_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    count = 0
    for i in range(message_id, 1, -1):
        try:
            await context.bot.delete_message(chat_id, i)
            count += 1
            if count >= 100: break
        except BadRequest: continue
    await update.message.reply_text(f"Đã dọn dẹp {count} tin nhắn gần nhất.")

async def clean_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except Exception as e:
        print(f"Không thể xóa tin nhắn hệ thống: {e}")
