from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import InputPeerChannel
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import pandas as pd
import asyncio
import os
from datetime import datetime

# Telegram API credentials
# Get these from https://my.telegram.org/apps
API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
PHONE_NUMBER = 'YOUR_PHONE_NUMBER'  # Your telegram phone number with country code
GROUP_LINK = 'YOUR_GROUP_LINK'  # Link or username of the group

async def main():
    print("Starting Telegram chat member parser...")
    
    # Create the client and connect
    client = TelegramClient('session_name', API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)
    
    if not await client.is_user_authorized():
        print("Authentication failed. Please check your credentials.")
        return

    try:
        # Get the chat entity
        chat = await client.get_entity(GROUP_LINK)
        
        # Initialize list to store member data
        all_participants = []
        
        # Get all participants
        offset = 0
        limit = 100
        
        while True:
            participants = await client(GetParticipantsRequest(
                channel=chat,
                filter=ChannelParticipantsSearch(''),
                offset=offset,
                limit=limit,
                hash=0
            ))
            
            if not participants.users:
                break
                
            all_participants.extend(participants.users)
            offset += len(participants.users)
            print(f"Fetched {len(all_participants)} members so far...")

        # Extract member information
        members_data = []
        for participant in all_participants:
            members_data.append({
                'Username': participant.username if participant.username else 'Not set',
                'First Name': participant.first_name if participant.first_name else 'Not set',
                'Last Name': participant.last_name if participant.last_name else 'Not set',
                'Phone': participant.phone if participant.phone else 'Not set',
                'Is Bot': participant.bot
            })

        # Create DataFrame and export to Excel
        df = pd.DataFrame(members_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'telegram_members_{timestamp}.xlsx'
        df.to_excel(output_file, index=False)
        
        print(f"\nSuccess! Data exported to {output_file}")
        print(f"Total members parsed: {len(members_data)}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main()) 