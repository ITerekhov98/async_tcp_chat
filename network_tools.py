import asyncio
import json
import time
from enum import Enum
from async_timeout import timeout

from additional_tools import Queues
from files_handling import update_config_file


class HandleReconnect():
    def __init__(self, max_attempts, time_to_break):
        self.max_attempts = max_attempts
        self.time_to_break = time_to_break
        self.attempts_count = 0

    def is_time_to_break(self):
        return self.max_attempts <= self.attempts_count

    def reset_attempts(self):
        self.attempts_count = 0


class ReadConnectionStateChanged(Enum):
    INITIATED = 'устанавливаем соединение'
    ESTABLISHED = 'соединение установлено'
    CLOSED = 'соединение закрыто'

    def __str__(self):
        return str(self.value)


class SendingConnectionStateChanged(Enum):
    INITIATED = 'устанавливаем соединение'
    ESTABLISHED = 'соединение установлено'
    CLOSED = 'соединение закрыто'

    def __str__(self):
        return str(self.value)


class NicknameReceived:
    def __init__(self, nickname):
        self.nickname = nickname


class InvalidToken(Exception):
    pass


async def receive_response(reader: asyncio.StreamReader):
    response = await reader.readline()
    decoded_response = response.decode()
    return decoded_response


async def write_with_drain(writer: asyncio.StreamWriter, message):
    writer.write(message.encode())
    await writer.drain()


async def read_messages(host, port, queues: Queues):
    queues.status_updates_queue.put_nowait(
        ReadConnectionStateChanged.INITIATED
    )
    reader, writer = await asyncio.open_connection(
        host,
        port
    )
    queues.status_updates_queue.put_nowait(
        ReadConnectionStateChanged.ESTABLISHED
    )
    try:
        while not reader.at_eof():
            message = await reader.readline()
            queues.messages_queue.put_nowait(message.decode())
            queues.saving_queue.put_nowait(message.decode())
            queues.watchdog_queue.put_nowait(
                'Connection is alive. New message in chat'
            )
    finally:
        queues.status_updates_queue.put_nowait(
            ReadConnectionStateChanged.CLOSED
        )


async def login(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        chat_hash_id):

    response = await receive_response(reader)
    if response.startswith('Hello'):
        writer.write(f'{chat_hash_id}\n'.encode())

    raw_user_info = await receive_response(reader)
    user_info = json.loads(raw_user_info)
    if not user_info:
        return

    response = await receive_response(reader)
    if response.startswith('Welcome'):
        return user_info['nickname']


async def handle_writing(
        host,
        port,
        chat_hash_id,
        queues: Queues):

    queues.status_updates_queue.put_nowait(
        SendingConnectionStateChanged.INITIATED
    )
    reader, writer = await asyncio.open_connection(host, port)
    queues.status_updates_queue.put_nowait(
        SendingConnectionStateChanged.ESTABLISHED
    )
    try:
        queues.watchdog_queue.put_nowait(
            'Connection is alive. Prompt before auth'
        )
        username = await login(reader, writer, chat_hash_id)
        if not username:
            raise InvalidToken
        queues.watchdog_queue.put_nowait(
            'Connection is alive. Authorization done'
        )
        queues.status_updates_queue.put_nowait(NicknameReceived(username))
        while True:
            message = await queues.sending_queue.get()
            await write_with_drain(writer, f"{message}\n\n")
            queues.watchdog_queue.put_nowait(
                'Connection is alive. Message sent'
            )
    finally:
        queues.status_updates_queue.put_nowait(
            SendingConnectionStateChanged.CLOSED
        )
        writer.close()


async def watch_for_connection(
        queues: Queues,
        reconnect: HandleReconnect,
        logger,
        reconnect_timeout):
    while True:
        try:
            async with timeout(reconnect_timeout):
                notice = await queues.watchdog_queue.get()
            reconnect.reset_attempts()
            logger.info(f'[{time.time()}] {notice}')
        except asyncio.exceptions.TimeoutError:
            raise ConnectionError


async def register(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        user_name):

    await reader.readline()
    await write_with_drain(writer, '\n')
    await receive_response(reader)

    await write_with_drain(writer, f'{user_name}\n')
    raw_user_info = await receive_response(reader)
    user_info = json.loads(raw_user_info)

    await update_config_file(user_info['account_hash'])
    return True
