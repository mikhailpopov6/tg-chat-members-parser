#!/usr/bin/env python3
"""
Telegram Channel Members Parser - Production Version
Combines original parser with ChannelVisor approach to bypass 200 participant limit

Features:
- Bypasses Telegram API 200 participant limit using search patterns
- Exports to Excel with detailed participant information
- Handles both channels and supergroups
- Includes error handling and rate limiting
- Production-ready with proper logging

Author: Based on ChannelVisor approach by Nikita Tolstoy
"""

import asyncio
import sys
import datetime
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsSearch
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_parser.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    # Try to import local configuration first (for development)
    from config_local import API_ID, API_HASH, PHONE_NUMBER, GROUP_LINK, SESSION_NAME
    logger.info("Using local configuration")
except ImportError:
    # Fall back to environment variables (for production)
    from config import API_ID, API_HASH, PHONE_NUMBER, GROUP_LINK, SESSION_NAME
    logger.info("Using environment variables configuration")

class TelegramMembersParser:
    def __init__(self):
        self.client = None
        self.all_participants = []
        self.unique_participants = set()
        
    async def get_subscribers_by_search(self, channel_entity, search_pattern):
        """Get subscribers using search pattern to bypass 200 limit"""
        participants = []
        offset = 0
        limit = 200
        
        logger.info(f"Searching for pattern: '{search_pattern}'")
        
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
                    logger.info(f"No more participants found for pattern '{search_pattern}' at offset {offset}")
                    break
                    
                participants.extend(response.users)
                offset += len(response.users)
                logger.info(f"Found {len(participants)} participants for pattern '{search_pattern}' so far...")
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
                # If we got fewer than requested, we've reached the end
                if len(response.users) < limit:
                    logger.info(f"Reached end for pattern '{search_pattern}'")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching participants for pattern '{search_pattern}' at offset {offset}: {str(e)}")
                break
        
        return participants

    async def parse_channel_members(self):
        """Main method to parse channel members"""
        logger.info("Starting Telegram channel members parser...")
        
        # Create the client and connect
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await self.client.start(phone=PHONE_NUMBER)
        
        if not await self.client.is_user_authorized():
            logger.error("Authentication failed. Please check your credentials.")
            return False

        try:
            # Get the channel entity
            logger.info("Connecting to the channel...")
            channel = await self.client.get_entity(GROUP_LINK)
            channel_title = getattr(channel, 'title', 'Unknown Channel')
            logger.info(f"Successfully connected to: {channel_title}")
            
            # Get full channel info
            full_channel = await self.client(GetFullChannelRequest(channel))
            total_participants = getattr(full_channel.full_chat, 'participants_count', 'Unknown')
            logger.info(f"Total participants in channel: {total_participants}")
            
            # Search patterns to get more participants (ChannelVisor approach)
            search_patterns = [''] + list('abcdefghijklmnopqrstuvwxyz') + list('0123456789')
            
            for pattern in search_patterns:
                participants = await self.get_subscribers_by_search(channel, pattern)
                
                # Add only unique participants
                new_participants = []
                for participant in participants:
                    if participant.id not in self.unique_participants:
                        self.unique_participants.add(participant.id)
                        new_participants.append(participant)
                
                self.all_participants.extend(new_participants)
                logger.info(f"Pattern '{pattern}' added {len(new_participants)} new unique participants. Total unique: {len(self.all_participants)}")
                
                # Add delay between patterns
                await asyncio.sleep(1)
            
            if not self.all_participants:
                logger.warning("No participants found.")
                return False

            # Extract participant information
            logger.info("Processing participant data...")
            participants_data = []
            for participant in self.all_participants:
                participants_data.append({
                    'User ID': participant.id,
                    'Username': participant.username if participant.username else 'Not set',
                    'First Name': participant.first_name if participant.first_name else 'Not set',
                    'Last Name': participant.last_name if participant.last_name else 'Not set',
                    'Phone': participant.phone if participant.phone else 'Not set',
                    'Is Bot': participant.bot,
                    'Verified': participant.verified,
                    'Premium': participant.premium,
                    'Access Hash': participant.access_hash
                })

            # Create DataFrame and export to Excel
            df = pd.DataFrame(participants_data)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'telegram_members_complete_{timestamp}.xlsx'
            df.to_excel(output_file, index=False)
            
            logger.info(f"Success! Data exported to {output_file}")
            logger.info(f"Total unique participants parsed: {len(participants_data)}")
            logger.info(f"Expected total participants: {total_participants}")
            
            # Calculate coverage percentage
            if isinstance(total_participants, int):
                coverage = (len(participants_data) / total_participants) * 100
                logger.info(f"Coverage: {coverage:.1f}%")
            
            return True

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return False
        
        finally:
            if self.client:
                await self.client.disconnect()

async def main():
    """Main entry point"""
    parser = TelegramMembersParser()
    success = await parser.parse_channel_members()
    
    if success:
        logger.info("Parsing completed successfully!")
        sys.exit(0)
    else:
        logger.error("Parsing failed!")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
