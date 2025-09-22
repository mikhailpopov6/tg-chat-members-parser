#!/usr/bin/env python3
"""
Enhanced Telegram Bot for Channel Members Parser
Beautiful interface with rich formatting and advanced features
"""

import asyncio
import logging
import sys
import datetime
import os
import json
from typing import Optional, List, Dict, Any
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsSearch
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from config_local import API_ID, API_HASH, PHONE_NUMBER, SESSION_NAME
    logger.info("Using local configuration")
except ImportError:
    from config import API_ID, API_HASH, PHONE_NUMBER, SESSION_NAME
    logger.info("Using environment variables configuration")

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

class EnhancedTelegramBot:
    def __init__(self):
        self.client = None
        self.active_parsers = {}
        
    async def start_telegram_client(self):
        """Initialize Telegram client"""
        try:
            self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            await self.client.start(phone=PHONE_NUMBER)
            
            if not await self.client.is_user_authorized():
                logger.error("Telegram client authentication failed")
                return False
                
            logger.info("Telegram client started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {str(e)}")
            return False

    def create_welcome_message(self) -> str:
        """Create beautiful welcome message"""
        return """
🎯 **Telegram Channel Members Parser Bot**

Добро пожаловать в продвинутый парсер участников Telegram каналов!

✨ **Возможности:**
• 📊 Парсинг до **95%+** участников канала
• 📁 Экспорт в **Excel** с красивым форматированием  
• 🔍 **Умный поиск** по различным критериям
• 📈 **Детальная статистика** и аналитика
• 🔒 **Безопасная** обработка данных
• ⚡ **Быстрая** работа с большими каналами

🚀 **Начните прямо сейчас!**
        """

    def create_channel_info_message(self, channel_info: Dict[str, Any]) -> str:
        """Create beautiful channel info message"""
        megagroup_icon = "🔗" if channel_info['is_megagroup'] else "📢"
        participants_count = f"{channel_info['participants_count']:,}"
        
        return f"""
{megagroup_icon} **Информация о канале**

📝 **Название:** `{channel_info['title']}`
👥 **Участников:** `{participants_count}`
🏷️ **Username:** `@{channel_info['username'] or 'Не указан'}`
🔧 **Тип:** `{'Супергруппа' if channel_info['is_megagroup'] else 'Канал'}`

⚡ **Готов к парсингу!**
        """

    def create_parsing_progress_message(self, pattern: str, progress: float, found: int) -> str:
        """Create parsing progress message"""
        progress_bar = self.create_progress_bar(progress)
        
        return f"""
🔄 **Парсинг в процессе...**

🔍 **Текущий паттерн:** `{pattern}`
📊 **Прогресс:** {progress_bar} `{progress:.1f}%`
👥 **Найдено участников:** `{found:,}`

⏳ *Пожалуйста, подождите...*
        """

    def create_progress_bar(self, progress: float, length: int = 10) -> str:
        """Create visual progress bar"""
        filled = int(progress / 100 * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"`{bar}`"

    def create_results_message(self, participants: List, channel_info: Dict[str, Any]) -> str:
        """Create beautiful results message"""
        total_found = len(participants)
        total_expected = channel_info['participants_count']
        coverage = (total_found / total_expected * 100) if total_expected > 0 else 0
        
        # Calculate statistics
        bots_count = sum(1 for p in participants if p.bot)
        verified_count = sum(1 for p in participants if p.verified)
        premium_count = sum(1 for p in participants if p.premium)
        
        return f"""
✅ **Парсинг завершен успешно!**

📊 **Результаты:**
• 👥 **Найдено участников:** `{total_found:,}`
• 📈 **Покрытие:** `{coverage:.1f}%`
• 🤖 **Ботов:** `{bots_count:,}`
• ✅ **Верифицированных:** `{verified_count:,}`
• ⭐ **Premium:** `{premium_count:,}`

📁 **Создаю Excel файл...**
        """

    def create_excel_export(self, participants: List, channel_title: str) -> str:
        """Create enhanced Excel export with beautiful formatting"""
        try:
            # Prepare data
            data = []
            for participant in participants:
                data.append({
                    'ID': participant.id,
                    'Username': participant.username or 'Не указан',
                    'Имя': participant.first_name or 'Не указано',
                    'Фамилия': participant.last_name or 'Не указано',
                    'Телефон': participant.phone or 'Не указан',
                    'Бот': '🤖 Да' if participant.bot else '👤 Нет',
                    'Верифицирован': '✅ Да' if participant.verified else '❌ Нет',
                    'Premium': '⭐ Да' if participant.premium else '❌ Нет',
                    'Дата парсинга': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Create filename
            safe_title = "".join(c for c in channel_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_title}_{timestamp}.xlsx"
            
            # Save to Excel with formatting
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Участники', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Участники']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return filename
        except Exception as e:
            logger.error(f"Error creating Excel export: {str(e)}")
            return None

    async def parse_channel_members_enhanced(self, channel_entity, user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced parsing with real-time updates"""
        try:
            search_patterns = [''] + list('abcdefghijklmnopqrstuvwxyz') + list('0123456789')
            
            all_participants = []
            unique_participants = set()
            total_patterns = len(search_patterns)
            
            # Initial progress message
            progress_msg = await update.message.reply_text("🔄 Инициализация парсинга...")
            
            for i, pattern in enumerate(search_patterns):
                # Update progress
                progress = (i / total_patterns) * 100
                participants = await self.get_subscribers_by_search(channel_entity, pattern)
                
                # Add only unique participants
                new_participants = []
                for participant in participants:
                    if participant.id not in unique_participants:
                        unique_participants.add(participant.id)
                        new_participants.append(participant)
                
                all_participants.extend(new_participants)
                
                # Update progress message every 5 patterns
                if i % 5 == 0 or i == total_patterns - 1:
                    progress_text = self.create_parsing_progress_message(
                        pattern, progress, len(all_participants)
                    )
                    await progress_msg.edit_text(progress_text, parse_mode=ParseMode.MARKDOWN)
                
                await asyncio.sleep(0.3)
            
            return {
                'participants': all_participants,
                'total_found': len(all_participants),
                'success': True,
                'progress_msg': progress_msg
            }
            
        except Exception as e:
            logger.error(f"Error parsing channel members: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def get_subscribers_by_search(self, channel_entity, search_pattern: str) -> List:
        """Get subscribers using search pattern"""
        participants = []
        offset = 0
        limit = 200
        
        while True:
            try:
                response = await self.client(GetParticipantsRequest(
                    channel=channel_entity,
                    filter=ChannelParticipantsSearch(search_pattern),
                    offset=offset,
                    limit=limit,
                    hash=0
                ))
                
                if not response.users:
                    break
                    
                participants.extend(response.users)
                offset += len(response.users)
                
                if len(response.users) < limit:
                    break
                    
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error in search pattern '{search_pattern}': {str(e)}")
                break
        
        return participants

# Bot handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    bot = EnhancedTelegramBot()
    welcome_text = bot.create_welcome_message()
    
    keyboard = [
        [InlineKeyboardButton("🔍 Парсить канал", callback_data="parse_channel")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats"),
         InlineKeyboardButton("❓ Справка", callback_data="help")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def parse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /parse command"""
    text = """
🔍 **Парсинг участников канала**

Отправьте ссылку на канал для парсинга участников.

**📋 Поддерживаемые форматы:**
• `https://t.me/channel_name`
• `@channel_name`  
• `t.me/channel_name`

**⚠️ Требования:**
• Вы должны быть **администратором** канала
• Канал должен быть **публичным** или у вас должны быть права на просмотр участников

**📤 Отправьте ссылку на канал:**
    """
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    context.user_data['waiting_for_channel'] = True

async def handle_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel link input with enhanced processing"""
    if not context.user_data.get('waiting_for_channel', False):
        return
    
    channel_link = update.message.text.strip()
    user_id = update.message.from_user.id
    
    # Clear waiting state
    context.user_data['waiting_for_channel'] = False
    
    # Show processing message
    processing_msg = await update.message.reply_text("🔄 Подключение к Telegram API...")
    
    try:
        # Initialize bot
        bot = EnhancedTelegramBot()
        
        # Start Telegram client
        if not await bot.start_telegram_client():
            await processing_msg.edit_text("❌ **Ошибка подключения к Telegram API**\n\nПроверьте настройки API ключей.")
            return
        
        # Get channel info
        await processing_msg.edit_text("🔍 Получаю информацию о канале...")
        channel_info = await bot.get_channel_info(channel_link)
        
        if not channel_info:
            await processing_msg.edit_text("❌ **Канал не найден или нет доступа**\n\nУбедитесь, что:\n• Ссылка на канал корректна\n• Вы являетесь администратором канала")
            await bot.client.disconnect()
            return
        
        # Show channel info
        info_text = bot.create_channel_info_message(channel_info)
        await processing_msg.edit_text(info_text, parse_mode=ParseMode.MARKDOWN)
        
        # Parse members with progress updates
        result = await bot.parse_channel_members_enhanced(channel_info['entity'], user_id, update, context)
        
        if not result['success']:
            await processing_msg.edit_text(f"❌ **Ошибка парсинга:** `{result['error']}`")
            await bot.client.disconnect()
            return
        
        participants = result['participants']
        progress_msg = result['progress_msg']
        
        # Show results
        results_text = bot.create_results_message(participants, channel_info)
        await progress_msg.edit_text(results_text, parse_mode=ParseMode.MARKDOWN)
        
        # Create Excel export
        excel_file = bot.create_excel_export(participants, channel_info['title'])
        
        if not excel_file:
            await progress_msg.edit_text("❌ **Ошибка создания Excel файла**")
            await bot.client.disconnect()
            return
        
        # Send Excel file
        with open(excel_file, 'rb') as file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file,
                filename=excel_file,
                caption=f"📊 **Участники канала '{channel_info['title']}'**\n\n"
                       f"👥 **Всего найдено:** `{len(participants):,}` участников\n"
                       f"📈 **Покрытие:** `{(len(participants) / channel_info['participants_count'] * 100):.1f}%`\n"
                       f"📅 **Дата парсинга:** `{datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}`",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Cleanup
        os.remove(excel_file)
        await bot.client.disconnect()
        
        # Show completion message
        keyboard = [
            [InlineKeyboardButton("🔍 Парсить другой канал", callback_data="parse_channel")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await progress_msg.edit_text(
            "🎉 **Парсинг завершен успешно!**\n\n📁 Excel файл отправлен.\n\nЧто делаем дальше?",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in channel parsing: {str(e)}")
        await processing_msg.edit_text(f"❌ **Произошла ошибка:** `{str(e)}`")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "parse_channel":
        await parse_command(update, context)
    elif query.data == "start":
        await start_command(update, context)
    elif query.data == "stats":
        await query.edit_message_text("📊 **Статистика**\n\nФункция в разработке...", parse_mode=ParseMode.MARKDOWN)
    elif query.data == "help":
        await query.edit_message_text("❓ **Справка**\n\nФункция в разработке...", parse_mode=ParseMode.MARKDOWN)
    elif query.data == "settings":
        await query.edit_message_text("⚙️ **Настройки**\n\nФункция в разработке...", parse_mode=ParseMode.MARKDOWN)

async def setup_bot_commands(application: Application):
    """Setup bot commands menu"""
    commands = [
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("parse", "🔍 Парсить канал"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    """Main function to run the enhanced bot"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Please set BOT_TOKEN environment variable or update the code")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("parse", parse_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_link))
    
    # Setup bot commands
    application.post_init = setup_bot_commands
    
    logger.info("Starting Enhanced Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
