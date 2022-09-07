import aiofiles
import os

from additional_tools import Queues


async def load_chat_history(filepath, messages_queue):
    if not os.path.exists(filepath):
        return
        
    async with aiofiles.open(filepath, 'r') as chat_file:
        chat_history = await chat_file.read()
    messages_queue.put_nowait(chat_history)


async def save_messages(filepath, queues: Queues):
    await load_chat_history(filepath, queues.messages_queue)

    async with aiofiles.open(filepath, 'a') as chat_file:
        while True:
            message = await queues.saving_queue.get()
            await chat_file.write(message)


async def update_config_file(chat_hash_id: str):
    filemode = 'r+' if os.path.exists('.env') else 'w+'
    async with aiofiles.open('.env', filemode) as f:
        config = await f.read()
        if 'CHAT_HASH_ID' not in config:
            await f.write(f"\nCHAT_HASH_ID={chat_hash_id}")
