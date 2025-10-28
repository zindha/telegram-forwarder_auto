import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Helper to split comma-separated and strip whitespace/items
def split_env_list(var):
    return [x.strip() for x in os.getenv(var, '').split(',') if x.strip()]

APP_ID = int(os.getenv('APP_ID'))
API_HASH = os.getenv('API_HASH')
SESSION = os.getenv('SESSION')
FROM_CHANNELS = split_env_list('FROM_CHANNEL')
TO_CHANNELS = split_env_list('TO_CHANNEL')
BLOCKED_TEXTS = split_env_list('BLOCKED_TEXTS')
WHITELIST_TEXTS = split_env_list('WHITELIST_TEXTS')
MEDIA_FORWARD_RESPONSE = os.getenv('MEDIA_FORWARD_RESPONSE', '')

# Use StringSession (CRITICAL for cloud deployment!)
client = TelegramClient(StringSession(SESSION), APP_ID, API_HASH)

# Convert channel strings to int if they look like IDs (handles usernames too)
def channel_parse(lst):
    return [int(x) if x.lstrip('-').isdigit() else x for x in lst]

@client.on(events.NewMessage(chats=channel_parse(FROM_CHANNELS)))
async def forward_handler(event):
    msg_text = event.message.message or ''
    # BLOCKLIST: Skip if contains a blocked word
    if any(bt.lower() in msg_text.lower() for bt in BLOCKED_TEXTS):
        return
    # WHITELIST: If present, only allow if contains a whitelist word
    if WHITELIST_TEXTS and not any(wt.lower() in msg_text.lower() for wt in WHITELIST_TEXTS):
        return
    for target in TO_CHANNELS:
        try:
            if event.message.media:
                await client.send_message(target, MEDIA_FORWARD_RESPONSE or '[Media message]')
            else:
                await client.send_message(target, msg_text)
        except Exception as e:
            print(f"Failed to forward to {target}: {e}")

if __name__ == '__main__':
    print(f"Bot starting: Forwarding from {FROM_CHANNELS} to {TO_CHANNELS}")
    with client:
        client.loop.run_forever()
