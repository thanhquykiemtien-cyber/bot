import time
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import ChatPermissions, Update
from telegram.ext import ContextTypes, filters
from config import ADMIN_IDS
from telegram.error import BadRequest

violation_db = defaultdict(lambda: defaultdict(lambda: {"violations": 0, "last_time": 0}))

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
    
    data["violations"] += 1
    if data["violations"] ==  1:
        await update.message.reply_text(f"⚠️ {user.first_name} vui lòng không gửi {reason} liên tục (Cảnh báo 1/3).")
    elif data["violations"] == 2:
        until = datetime.now() + timedelta(hours=2)
        await context.bot.restrict_chat_member(chat_id, user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await update.message.reply_text(f"⚠️ {user.first_name} đã bị khóa chat 2h vì cố tình {reason} (Cảnh báo 2/3).")
    elif data["violations"] >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        await update.message.reply_text(f"🚫 {user.first_name} đã bị BAN vĩnh viễn khỏi nhóm vì spam {reason} quá nhiều lần.")

async def anti_spam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await is_admin(update, context): return
    msg = update.message
    
    if msg.entities and any(e.type == 'url' for e in msg.entities):
        await punish_user(update, context, "Liên kết (Link)")
    elif msg.photo:
        await punish_user(update, context, "Hình ảnh")
    elif msg.video or msg.animation:
        await punish_user(update, context, "Video/GIF")
    elif msg.sticker:
        await punish_user(update, context, "Sticker")
        
async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except BadRequest:
            pass

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        except BadRequest:
            pass

async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        until = datetime.now() + timedelta(hours=2)
        try:
            await context.bot.restrict_chat_member(update.effective_chat.id, user_id, ChatPermissions(can_send_messages=False), until_date=until)
            await update.message.reply_text("Đã khóa chat thành viên trong 2h.")
        except BadRequest:
            pass

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user.id)
            await update.message.reply_text(f"🚫 Đã BAN vĩnh viễn {user.first_name}.")
        except BadRequest:
            pass
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
        except BadRequest:
            continue
    await update.message.reply_text(f"Đã dọn dẹp {count} tin nhắn gần nhất.")

async def clean_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except Exception as e:
        print(f"Không thể xóa tin nhắn hệ thống: {e}")