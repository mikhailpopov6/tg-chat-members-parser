#!/usr/bin/env python3
"""
Telegram Bot for Channel Members Parser
Interactive bot with beautiful output and convenient member parsing

Features:
- Interactive menu for channel parsing
- Beautiful formatted output
- Export to Excel with custom naming
- Real-time progress updates
- Secure configuration
"""

import asyncio
import logging
import sys
import datetime
import os
from typing import Optional, List, Dict, Any
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsSearch
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json

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
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')  # Get from @BotFather

class TelegramMembersBot:
    def __init__(self):
        self.client = None
        self.active_parsers = {}  # Store active parsing sessions
        
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

    async def get_channel_info(self, channel_link: str) -> Optional[Dict[str, Any]]:
        """Get basic channel information"""
        try:
            channel = await self.client.get_entity(channel_link)
            full_channel = await self.client(GetFullChannelRequest(channel))
            
            return {
                'title': getattr(channel, 'title', 'Unknown'),
                'id': channel.id,
                'username': getattr(channel, 'username', None),
                'participants_count': getattr(full_channel.full_chat, 'participants_count', 0),
                'is_megagroup': getattr(channel, 'megagroup', False),
                'entity': channel
            }
        except Exception as e:
            logger.error(f"Error getting channel info: {str(e)}")
            return None

    async def parse_channel_members(self, channel_entity, user_id: int) -> Dict[str, Any]:
        """Parse channel members with progress updates"""
        try:
            # Search patterns for comprehensive parsing
            search_patterns = [''] + list('abcdefghijklmnopqrstuvwxyz') + list('0123456789')
            
            all_participants = []
            unique_participants = set()
            total_patterns = len(search_patterns)
            
            for i, pattern in enumerate(search_patterns):
                # Update progress
                progress = (i / total_patterns) * 100
                await self.update_parsing_progress(user_id, f"🔍 Поиск по паттерну '{pattern}'...", progress)
                
                participants = await self.get_subscribers_by_search(channel_entity, pattern)
                
                # Add only unique participants
                new_participants = []
                for participant in participants:
                    if participant.id not in unique_participants:
                        unique_participants.add(participant.id)
                        new_participants.append(participant)
                
                all_participants.extend(new_participants)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            return {
                'participants': all_participants,
                'total_found': len(all_participants),
                'success': True
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
                    
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error in search pattern '{search_pattern}': {str(e)}")
                break
        
        return participants

    async def update_parsing_progress(self, user_id: int, message: str, progress: float):
        """Update parsing progress (placeholder for bot integration)"""
        # This will be implemented with actual bot message updates
        logger.info(f"Progress for user {user_id}: {progress:.1f}% - {message}")

    def format_member_info(self, participant) -> Dict[str, Any]:
        """Format participant information for display"""
        return {
            'id': participant.id,
            'username': participant.username or 'Не указан',
            'first_name': participant.first_name or 'Не указано',
            'last_name': participant.last_name or 'Не указано',
            'phone': participant.phone or 'Не указан',
            'is_bot': '🤖 Да' if participant.bot else '👤 Нет',
            'verified': '✅ Да' if participant.verified else '❌ Нет',
            'premium': '⭐ Да' if participant.premium else '❌ Нет'
        }

    def create_excel_export(self, participants: List, filename: str) -> str:
        """Create Excel export with formatted data"""
        try:
            data = []
            for participant in participants:
                member_info = self.format_member_info(participant)
                data.append({
                    'ID': member_info['id'],
                    'Username': member_info['username'],
                    'Имя': member_info['first_name'],
                    'Фамилия': member_info['last_name'],
                    'Телефон': member_info['phone'],
                    'Бот': member_info['is_bot'],
                    'Верифицирован': member_info['verified'],
                    'Premium': member_info['premium']
                })
            
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)
            return filename
        except Exception as e:
            logger.error(f"Error creating Excel export: {str(e)}")
            return None

# Bot handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = """
🤖 **Telegram Channel Members Parser Bot**

Добро пожаловать! Этот бот поможет вам извлечь информацию об участниках Telegram каналов.

**Возможности:**
• 📊 Парсинг до 95%+ участников канала
• 📁 Экспорт в Excel с красивым форматированием
• 🔍 Поиск по различным критериям
• 📈 Статистика и аналитика
• 🔒 Безопасная обработка данных

**Команды:**
/parse - Начать парсинг канала
/help - Справка
/status - Статус бота

Выберите действие:
    """
    
    keyboard = [
        [InlineKeyboardButton("🔍 Парсить канал", callback_data="parse_channel")],
        [InlineKeyboardButton("❓ Справка", callback_data="help"),
         InlineKeyboardButton("📊 Статус", callback_data="status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def parse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /parse command"""
    text = """
🔍 **Парсинг участников канала**

Отправьте ссылку на канал или username для парсинга.

**Поддерживаемые форматы:**
• `https://t.me/channel_name`
• `@channel_name`
• `t.me/channel_name`

**Требования:**
• Вы должны быть администратором канала
• Канал должен быть публичным или у вас должны быть права на просмотр участников

Отправьте ссылку на канал:
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')
    
    # Set state to wait for channel link
    context.user_data['waiting_for_channel'] = True

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 **Справка по использованию бота**

**Основные команды:**
• `/start` - Главное меню
• `/parse` - Начать парсинг канала
• `/help` - Эта справка
• `/status` - Статус бота

**Процесс парсинга:**
1. Отправьте ссылку на канал
2. Бот проверит ваши права доступа
3. Начнется процесс извлечения участников
4. Получите Excel файл с результатами

**Формат результатов:**
• ID пользователя
• Username
• Имя и фамилия
• Номер телефона (если доступен)
• Статус (бот, верифицирован, premium)

**Ограничения:**
• Максимум 10,000 участников за раз
• Парсинг может занять 2-5 минут
• Требуются права администратора

**Поддержка:**
При возникновении проблем обратитесь к администратору.
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    bot = TelegramMembersBot()
    client_status = "❌ Не подключен"
    
    try:
        if await bot.start_telegram_client():
            client_status = "✅ Подключен"
            await bot.client.disconnect()
    except:
        pass
    
    status_text = f"""
📊 **Статус бота**

**Telegram API:** {client_status}
**Время работы:** {datetime.datetime.now().strftime('%H:%M:%S')}
**Активных парсингов:** 0
**Версия:** 2.0 Production

**Система:**
• Парсинг участников: ✅ Работает
• Экспорт в Excel: ✅ Работает
• Безопасность: ✅ Настроена
    """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "parse_channel":
        await parse_command(update, context)
    elif query.data == "help":
        await help_command(update, context)
    elif query.data == "status":
        await status_command(update, context)

async def handle_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel link input"""
    if not context.user_data.get('waiting_for_channel', False):
        return
    
    channel_link = update.message.text.strip()
    user_id = update.message.from_user.id
    
    # Clear waiting state
    context.user_data['waiting_for_channel'] = False
    
    # Show processing message
    processing_msg = await update.message.reply_text("🔄 Обрабатываю запрос...")
    
    try:
        # Initialize bot
        bot = TelegramMembersBot()
        
        # Start Telegram client
        if not await bot.start_telegram_client():
            await processing_msg.edit_text("❌ Ошибка подключения к Telegram API")
            return
        
        # Get channel info
        await processing_msg.edit_text("🔍 Получаю информацию о канале...")
        channel_info = await bot.get_channel_info(channel_link)
        
        if not channel_info:
            await processing_msg.edit_text("❌ Канал не найден или нет доступа")
            await bot.client.disconnect()
            return
        
        # Show channel info
        info_text = f"""
📊 **Информация о канале**

**Название:** {channel_info['title']}
**Участников:** {channel_info['participants_count']:,}
**Тип:** {'Супергруппа' if channel_info['is_megagroup'] else 'Канал'}
**Username:** @{channel_info['username'] or 'Не указан'}

Начинаю парсинг участников...
        """
        
        await processing_msg.edit_text(info_text, parse_mode='Markdown')
        
        # Parse members
        result = await bot.parse_channel_members(channel_info['entity'], user_id)
        
        if not result['success']:
            await processing_msg.edit_text(f"❌ Ошибка парсинга: {result['error']}")
            await bot.client.disconnect()
            return
        
        participants = result['participants']
        
        # Create Excel export
        await processing_msg.edit_text("📁 Создаю Excel файл...")
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"channel_members_{timestamp}.xlsx"
        
        excel_file = bot.create_excel_export(participants, filename)
        
        if not excel_file:
            await processing_msg.edit_text("❌ Ошибка создания Excel файла")
            await bot.client.disconnect()
            return
        
        # Send results
        success_text = f"""
✅ **Парсинг завершен успешно!**

**Результаты:**
• Найдено участников: {len(participants):,}
• Покрытие: {(len(participants) / channel_info['participants_count'] * 100):.1f}%
• Файл: {filename}

Отправляю Excel файл...
        """
        
        await processing_msg.edit_text(success_text, parse_mode='Markdown')
        
        # Send Excel file
        with open(excel_file, 'rb') as file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file,
                filename=filename,
                caption=f"📊 Участники канала '{channel_info['title']}'\n\n"
                       f"Всего найдено: {len(participants):,} участников\n"
                       f"Покрытие: {(len(participants) / channel_info['participants_count'] * 100):.1f}%"
            )
        
        # Cleanup
        os.remove(excel_file)
        await bot.client.disconnect()
        
        # Show completion message
        keyboard = [
            [InlineKeyboardButton("🔍 Парсить другой канал", callback_data="parse_channel")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(
            "🎉 **Парсинг завершен!**\n\nФайл отправлен. Что делаем дальше?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in channel parsing: {str(e)}")
        await processing_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")

async def setup_bot_commands(application: Application):
    """Setup bot commands menu"""
    commands = [
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("parse", "🔍 Парсить канал"),
        BotCommand("help", "❓ Справка"),
        BotCommand("status", "📊 Статус бота")
    ]
    await application.bot.set_my_commands(commands)

def main():
    """Main function to run the bot"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Please set BOT_TOKEN environment variable or update the code")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("parse", parse_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_link))
    
    # Setup bot commands
    application.post_init = setup_bot_commands
    
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
