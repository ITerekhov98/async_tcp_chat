import asyncio
import aiofiles
import json
import logging
import os

from additional_tools import get_config

logger = logging.getLogger(__name__)


async def receive_response(reader: asyncio.StreamReader):
    response = await reader.readline()
    decoded_response = response.decode()
    logger.info(decoded_response)
    return decoded_response


async def register(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        user_name=None):

    await reader.readline()
    if not user_name:    
        user_name = input()
    else:
        writer.write('\n'.encode())
        await receive_response(reader)

    writer.write(f'{user_name}\n'.encode())
    raw_user_info = await receive_response(reader)
    user_info = json.loads(raw_user_info)

    filemode = 'r+' if os.path.exists('.env') else 'w+'
    async with aiofiles.open('.env', filemode) as f:
            config = await f.read()
            if 'CHAT_HASH_ID' not in config:
                await f.write(f"\nCHAT_HASH_ID={user_info['account_hash']}")

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
        logger.warning('Cannot log in. Broken token.')
        print(
            'Не можем идентифицировать токен. '
            'Проверьте правильность указанного токена'
            'и перезапустите программу,\r\n'
            'либо укажите никнейм для повторной регистрации:\r\n'
        )
        return await register(reader, writer)

    response = await receive_response(reader)
    if response.startswith('Welcome'):
        return True
    return False


async def handle_writing(config: dict):
    reader, writer = await asyncio.open_connection(
        config['host'],
        config['port']
    )
    if user_name := config.get('username'):
        await register(reader, writer, user_name)
    else:
        is_login = await login(reader, writer, config['chat_hash_id'])
        if not is_login:
            logger.warning('Error occurred while trying to log in')
            print('Не можем подключиться к чату. Попробуйте чуть позже')
            writer.close()
            return

    writer.write(f"{config['message']}\n\n".encode())
    await writer.drain()
    print('Ваше сообщение отправлено!')
    logger.info(f"Отправлено сообщение: {config['message']}")
    writer.close()
    return


if __name__ == '__main__':
    logging.basicConfig(
        filename='logfile.log',
        filemode='a',
        format='%(levelname)s : %(name)s : %(message)s',
        level=logging.INFO
    )
    config = get_config('write')
    asyncio.run(handle_writing(config))
