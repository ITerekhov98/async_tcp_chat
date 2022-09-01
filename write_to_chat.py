import asyncio
import aiofiles
import json
import logging
import os
from enum import Enum

from additional_tools import get_config


logger = logging.getLogger(__name__)


class InvalidToken(Exception):
    pass


class SendingConnectionStateChanged(Enum):
    INITIATED = 'устанавливаем соединение'
    ESTABLISHED = 'соединение установлено'
    CLOSED = 'соединение закрыто'

    def __str__(self):
        return str(self.value)


class NicknameReceived:
    def __init__(self, nickname):
        self.nickname = nickname


async def receive_response(reader: asyncio.StreamReader):
    response = await reader.readline()
    decoded_response = response.decode()
    logger.info(decoded_response)
    return decoded_response


async def update_config_file(chat_hash_id: str):
    filemode = 'r+' if os.path.exists('.env') else 'w+'
    async with aiofiles.open('.env', filemode) as f:
        config = await f.read()
        if 'CHAT_HASH_ID' not in config:
            await f.write(f"\nCHAT_HASH_ID={chat_hash_id}")


async def write_with_drain(writer: asyncio.StreamWriter, message):
    writer.write(message.encode())
    await writer.drain()


async def get_username_from_user():
    print(
        'Не можем идентифицировать токен. '
        'Проверьте правильность указанного токена '
        'и перезапустите программу,\r\n'
        'либо укажите никнейм для повторной регистрации:\r\n'
    )
    return input()


async def register(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        user_name=None):

    if not user_name:
        user_name = await get_username_from_user()
    else:
        await reader.readline()
        await write_with_drain(writer, '\n')
    await receive_response(reader)

    await write_with_drain(writer, f'{user_name}\n')
    raw_user_info = await receive_response(reader)
    user_info = json.loads(raw_user_info)

    await update_config_file(user_info['account_hash'])
    logger.info(f"user {user_info['nickname']} successfully register")
    print(f"Добро пожаловать, {user_info['nickname']}!\r\n")
    return True


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
        sending_queue: asyncio.Queue,
        status_updates_queue: asyncio.Queue,
        watchdog_queue: asyncio.Queue):

    status_updates_queue.put_nowait(SendingConnectionStateChanged.INITIATED)
    reader, writer = await asyncio.open_connection(host, port)
    status_updates_queue.put_nowait(SendingConnectionStateChanged.ESTABLISHED)
    try:
        watchdog_queue.put_nowait('Connection is alive. Prompt before auth')
        username = await login(reader, writer, chat_hash_id)
        if not username:
            raise InvalidToken
        watchdog_queue.put_nowait('Connection is alive. Authorization done')
        status_updates_queue.put_nowait(NicknameReceived(username))
        while True:
            message = await sending_queue.get()
            await write_with_drain(writer, f"{message}\n\n")
            watchdog_queue.put_nowait('Connection is alive. Message sent')

    finally:
        status_updates_queue.put_nowait(SendingConnectionStateChanged.CLOSED)
        writer.close()


# async def handle_writing(
#         host,
#         port,
#         message,
#         chat_hash_id,
#         username):

#     reader, writer = await asyncio.open_connection(host, port)
#     try:
#         if username:
#             await register(reader, writer, username)
#         else:
#             is_login = await login(reader, writer, chat_hash_id)
#             if not is_login:
#                 logger.warning('Error occurred while trying to log in')
#                 print('Не можем подключиться к чату. Попробуйте чуть позже')
#                 writer.close()
#                 return

#         await write_with_drain(writer, f"{message}\n\n")
#         print('Ваше сообщение отправлено!')
#         logger.info(f"Отправлено сообщение: {message}")
#     finally:
#         writer.close()


if __name__ == '__main__':
    logging.basicConfig(
        filename='logfile.log',
        filemode='a',
        format='%(levelname)s : %(name)s : %(message)s',
        level=logging.INFO
    )
    config = get_config('write')
    host = config['host']
    port = config['port']
    message = config['message']
    chat_hash_id = config['chat_hash_id']
    username = config.get('username')
    asyncio.run(
        handle_writing(
            host,
            port,
            message,
            chat_hash_id,
            username
        )
    )
