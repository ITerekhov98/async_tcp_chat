import asyncio
import aiofiles

from enum import Enum


class ReadConnectionStateChanged(Enum):
    INITIATED = 'устанавливаем соединение'
    ESTABLISHED = 'соединение установлено'
    CLOSED = 'соединение закрыто'

    def __str__(self):
        return str(self.value)


async def read_messages(host, port, messages_queue: asyncio.Queue, saving_queue: asyncio.Queue, status_updates_queue: asyncio.Queue, watchdog_queue: asyncio.Queue):
    status_updates_queue.put_nowait(ReadConnectionStateChanged.INITIATED)
    reader, writer = await asyncio.open_connection(
        host,
        port
    )
    status_updates_queue.put_nowait(ReadConnectionStateChanged.ESTABLISHED)
    try:
        while not reader.at_eof():
            message = await reader.readline()
            messages_queue.put_nowait(message.decode())
            saving_queue.put_nowait(message.decode())
            watchdog_queue.put_nowait('Connection is alive. New message in chat')
    finally:
            status_updates_queue.put_nowait(ReadConnectionStateChanged.CLOSED)
        

async def get_chat_history(filepath):
    async with aiofiles.open(filepath, 'r') as chat_file:
        chat_history = await chat_file.read()
    return chat_history


async def save_messages(filepath, saving_queue: asyncio.Queue, messages_queue: asyncio.Queue):
    chat_history = await get_chat_history(filepath)
    messages_queue.put_nowait(chat_history)
    async with aiofiles.open(filepath, 'a') as chat_file:
        while True:
            message = await saving_queue.get()
            await chat_file.write(message)