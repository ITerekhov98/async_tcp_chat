import asyncio
from environs import Env
import logging
import json
import aiofiles

logger = logging.getLogger(__name__)


async def receive_response(reader: asyncio.StreamReader):
    response = await reader.readline()
    decoded_response = response.decode()
    logger.info(decoded_response)
    return decoded_response


async def register(reader: asyncio.StreamReader, writer:asyncio.StreamWriter):
    await reader.readline()
    user_name = input()
    writer.write(f'{user_name}\n'.encode())
    raw_user_info = await receive_response(reader)
    user_info = json.loads(raw_user_info)

    async with aiofiles.open('.env', 'a') as f:
        await f.write(f"CHAT_HASH_ID={user_info['account_hash']}")

    logger.info(f"user {user_info['nickname']} successfully register")
    print(f"Добро пожаловать, {user_info['nickname']}!\r\n")
    return True


async def login(reader: asyncio.StreamReader, writer:asyncio.StreamWriter, chat_hash_id):
    response = await receive_response(reader)
    if response.startswith('Hello'):
        writer.write(f'{chat_hash_id}\n'.encode())

    raw_user_info = await receive_response(reader)
    user_info = json.loads(raw_user_info)
    if not user_info:
        logger.warning('Cannot log in. Broken token.')
        print(
            'Не можем идентифицировать токен. '
            'Проверьте правильность указанного токена и перезапустите программу,\r\n'
            'либо укажите никнейм для повторной регистрации:\r\n'
        )
        return await register(reader, writer)

    response = await receive_response(reader)
    if response.startswith('Welcome'):
        return True  
    return False


async def handle_writing(chat_hash_id):
    reader, writer = await asyncio.open_connection(
        'minechat.dvmn.org', 5050)

    is_login = await login(reader, writer, chat_hash_id)
    if not is_login:
        logger.warning('Error occurred while trying to log in')
        print('Не можем подключиться к чату. Попробуйте чуть позже')
        writer.close()
        return

    while True:
        message = input('Введите текст сообщения:\r\n')
        writer.write(f'{message}\n\n'.encode())
        await writer.drain()
        print('Ваше сообщение отправлено!')
        logger.info(f'Отправлено сообщение: {message}')
        await receive_response(reader)


if __name__ == '__main__':
    logging.basicConfig(
        filename='logfile.log',
        filemode='a',
        format='%(levelname)s : %(name)s : %(message)s',
        level=logging.INFO
    )
    env = Env()
    env.read_env()
    chat_hash_id = env.str('CHAT_HASH_ID', None)
    asyncio.run(handle_writing(chat_hash_id))