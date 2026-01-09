import os
import asyncio
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from asgiref.sync import sync_to_async
from videos.models import Video, Category

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# States for Add Video Conversation
VIDEO, TITLE_LAT, TITLE_KIRIL, TITLE_RU, DESC_LAT, DESC_KIRIL, DESC_RU, CATEGORY, VIDEO_NEW_CATEGORY, CONFIRM = range(10)
# States for Add Category Conversation
ADD_CATEGORY_NAME = range(10, 11)

class Command(BaseCommand):
    help = 'Runs the Telegram Bot'

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token or token == 'YOUR_BOT_TOKEN':
            self.stdout.write(self.style.ERROR('TELEGRAM_BOT_TOKEN is not set in settings.'))
            return

        import asyncio
        try:
            asyncio.run(self.run_bot(token))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Bot stopped by user.'))

    async def run_bot(self, token):
        application = ApplicationBuilder().token(token).build()

        # Add Video Conversation
        add_video_conv = ConversationHandler(
            entry_points=[
                CommandHandler('addvideo', self.add_video_start),
                MessageHandler(filters.Regex('^➕ Add Video$'), self.add_video_start)
            ],
            states={
                VIDEO: [MessageHandler(filters.VIDEO, self.receive_video)],
                TITLE_LAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_title_lat)],
                TITLE_KIRIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_title_kiril)],
                TITLE_RU: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_title_ru)],
                DESC_LAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_desc_lat)],
                DESC_KIRIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_desc_kiril)],
                DESC_RU: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_desc_ru)],
                CATEGORY: [CallbackQueryHandler(self.receive_category)],
                VIDEO_NEW_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_new_category_inline)],
                CONFIRM: [CallbackQueryHandler(self.confirm_save)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        # Add Category Conversation
        add_category_conv = ConversationHandler(
            entry_points=[
                CommandHandler('addcategory', self.add_category_start),
                MessageHandler(filters.Regex('^➕ Add Category$'), self.add_category_start)
            ],
            states={
                ADD_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_new_category)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('listvideos', self.list_videos))
        application.add_handler(MessageHandler(filters.Regex('^📋 List Videos$'), self.list_videos))
        
        application.add_handler(add_video_conv)
        application.add_handler(add_category_conv)
        
        # Global handler must be last to allow conversations to handle their own callbacks first
        application.add_handler(CallbackQueryHandler(self.handle_callback))

        self.stdout.write(self.style.SUCCESS('Starting bot...'))
        
        # Manual lifecycle management to avoid initialization errors
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Keep running until stopped
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

    async def is_admin(self, update: Update):
        user_id = update.effective_user.id
        if user_id not in settings.ADMIN_IDS:
            self.stdout.write(self.style.WARNING(f"Unauthorized access attempt from User ID: {user_id}"))
            await update.message.reply_text(f"⛔ You are not authorized. Your ID is: {user_id}")
            return False
        return True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(update): return
        
        keyboard = [
            ['➕ Add Video', '📋 List Videos'],
            ['➕ Add Category']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "👋 Welcome to IshoraTech Admin Bot!\n"
            "Select an option below:",
            reply_markup=reply_markup
        )

    async def check_if_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text in ['➕ Add Video', '📋 List Videos', '➕ Add Category']:
            await update.message.reply_text("🔄 Switching context... Please click the button again to confirm.")
            context.user_data.clear()
            return True
        return False

    # --- Add Category Flow ---
    async def add_category_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(update): return ConversationHandler.END
        await update.message.reply_text("Please enter the name of the new category:")
        return ADD_CATEGORY_NAME

    async def receive_new_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Standalone /addcategory command handler
        if await self.check_if_menu_command(update, context):
            return ConversationHandler.END
            
        category_name = update.message.text
        
        exists = await sync_to_async(Category.objects.filter(name=category_name).exists)()
        if exists:
            await update.message.reply_text(f"Category '{category_name}' already exists.")
            return ConversationHandler.END

        await sync_to_async(Category.objects.create)(name=category_name)
        await update.message.reply_text(f"✅ Category '{category_name}' created successfully!")
        return ConversationHandler.END

    # --- Add Video Flow ---
    async def add_video_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(update): return ConversationHandler.END
        await update.message.reply_text("Please upload the video file:")
        return VIDEO

    async def receive_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        video = update.message.video
        context.user_data['file_id'] = video.file_id
        await update.message.reply_text("Video received.\n\n1️⃣ Enter Title (Latin):")
        return TITLE_LAT

    async def receive_title_lat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_if_menu_command(update, context): return ConversationHandler.END
        context.user_data['title_lat'] = update.message.text
        await update.message.reply_text("2️⃣ Enter Title (Cyrillic):")
        return TITLE_KIRIL

    async def receive_title_kiril(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_if_menu_command(update, context): return ConversationHandler.END
        context.user_data['title_kiril'] = update.message.text
        await update.message.reply_text("3️⃣ Enter Title (Russian) - or type 'skip':")
        return TITLE_RU

    async def receive_title_ru(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_if_menu_command(update, context): return ConversationHandler.END
        text = update.message.text
        context.user_data['title_ru'] = "" if text.lower() == 'skip' else text
        await update.message.reply_text("4️⃣ Enter Description (Latin):")
        return DESC_LAT

    async def receive_desc_lat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_if_menu_command(update, context): return ConversationHandler.END
        context.user_data['desc_lat'] = update.message.text
        await update.message.reply_text("5️⃣ Enter Description (Cyrillic):")
        return DESC_KIRIL

    async def receive_desc_kiril(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_if_menu_command(update, context): return ConversationHandler.END
        context.user_data['desc_kiril'] = update.message.text
        await update.message.reply_text("6️⃣ Enter Description (Russian) - or type 'skip':")
        return DESC_RU

    async def receive_desc_ru(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_if_menu_command(update, context): return ConversationHandler.END
        text = update.message.text
        context.user_data['desc_ru'] = "" if text.lower() == 'skip' else text
        
        # Fetch categories for Inline Keyboard
        categories = await sync_to_async(list)(Category.objects.all())
        
        keyboard = []
        for c in categories:
            keyboard.append([InlineKeyboardButton(c.name, callback_data=f"cat_{c.id}")])
        
        # Add "New Category" button
        keyboard.append([InlineKeyboardButton("➕ New Category", callback_data="cat_new")])
            
        await update.message.reply_text(
            "7️⃣ Select a Category or create a new one:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CATEGORY

    async def receive_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Handle New Category creation
        if data == "cat_new":
            await query.edit_message_text("Please enter the name of the new category:")
            return VIDEO_NEW_CATEGORY
            
        if not data.startswith("cat_"):
            return CATEGORY
            
        cat_id = int(data.split("_")[1])
        category = await sync_to_async(Category.objects.get)(id=cat_id)
        context.user_data['category_id'] = category.id
        context.user_data['category_name'] = category.name

        return await self.show_confirmation(query, context)

    async def receive_new_category_inline(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Inline category creation during video upload
        category_name = update.message.text
        
        # Check if exists
        category, created = await sync_to_async(Category.objects.get_or_create)(name=category_name)
        
        context.user_data['category_id'] = category.id
        context.user_data['category_name'] = category.name
        
        await update.message.reply_text(f"✅ Category '{category_name}' created and selected.")
        
        return await self.show_confirmation(update, context)

    async def show_confirmation(self, update_or_query, context):
        # Handle both Message (from inline creation) and CallbackQuery (from selection)
        if hasattr(update_or_query, 'message'):
            message = update_or_query.message
        else:
            message = update_or_query # It's already a message object if passed from receive_new_category_inline? No, update.message is the message.
        
        # Wait, show_confirmation needs to reply.
        # If called from receive_category (CallbackQuery), we use query.edit_message_text
        # If called from receive_new_category_inline (Message), we use update.message.reply_text
        
        summary = (
            f"Title (Lat): {context.user_data.get('title_lat')}\n"
            f"Title (Kir): {context.user_data.get('title_kiril')}\n"
            f"Category: {context.user_data.get('category_name')}\n\n"
            "Save this video?"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Save", callback_data="confirm_yes")],
            [InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")]
        ]
        
        if isinstance(update_or_query, Update):
             await update_or_query.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
             # It's a CallbackQuery
             await update_or_query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
             
        return CONFIRM

    async def confirm_save(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == 'confirm_yes':
            category = await sync_to_async(Category.objects.get)(id=context.user_data['category_id'])
            await sync_to_async(Video.objects.create)(
                title_lat=context.user_data['title_lat'],
                title_kiril=context.user_data['title_kiril'],
                title_ru=context.user_data['title_ru'],
                description_lat=context.user_data['desc_lat'],
                description_kiril=context.user_data['desc_kiril'],
                description_ru=context.user_data['desc_ru'],
                category=category,
                telegram_file_id=context.user_data['file_id'],
                is_published=True
            )
            await query.edit_message_text("✅ Video saved and published!")
        else:
            await query.edit_message_text("❌ Operation cancelled.")
        
        context.user_data.clear()
        await self.show_main_menu(query.message, context)
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Operation cancelled.")
        context.user_data.clear()
        await self.show_main_menu(update.message, context)
        return ConversationHandler.END

    async def show_main_menu(self, message, context):
        keyboard = [
            ['➕ Add Video', '📋 List Videos'],
            ['➕ Add Category']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await message.reply_text("Select an option:", reply_markup=reply_markup)

    # --- List & Delete ---
    async def list_videos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(update): return
        
        videos = await sync_to_async(list)(Video.objects.all().select_related('category').order_by('-created_at'))
        if not videos:
            await update.message.reply_text("No videos found.")
            return

        await update.message.reply_text("📺 **Video List**:")
        
        for v in videos:
            keyboard = [[InlineKeyboardButton("❌ Delete", callback_data=f"delete_{v.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"ID: {v.id}\nTitle: {v.title_lat}\nCategory: {v.category.name}",
                reply_markup=reply_markup
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if not await self.is_admin(update): return

        data = query.data

        if data.startswith("delete_"):
            video_id = int(data.split("_")[1])
            try:
                video = await sync_to_async(Video.objects.get)(id=video_id)
                await sync_to_async(video.delete)()
                await query.edit_message_text(text=f"✅ Video '{video.title_lat}' (ID: {video_id}) deleted.")
            except Video.DoesNotExist:
                await query.edit_message_text(text="❌ Video not found or already deleted.")
        elif data.startswith("cat_") or data == "cat_new":
            # If we are here, it means the ConversationHandler didn't catch it.
            # This happens if the bot was restarted and the state was lost.
            await query.edit_message_text(
                text="⚠️ **Session Expired**\n\n"
                     "The bot was restarted, and your previous session is no longer active.\n"
                     "Please start the process again by clicking '➕ Add Video' in the main menu."
            )
