import asyncio
from environs import Env
import logging


logger = logging.getLogger(__name__)


async def receive_response(reader: asyncio.StreamReader):
    response = await reader.readline()
    decoded_response = response.decode()
    logger.info(decoded_response)
    return decoded_response


async def login(reader: asyncio.StreamReader, writer:asyncio.StreamWriter, chat_hash_id):
    
    response = await receive_response(reader)
    if response.startswith('Hello'):
        writer.write(f'{chat_hash_id}\n'.encode())

    user_info = await receive_response(reader)

    response = await receive_response(reader)
    if response.startswith('Welcome'):
        return True
    return False

async def handle_writing(chat_hash_id):
    reader, writer = await asyncio.open_connection(
        'minechat.dvmn.org', 5050)

    if await login(reader, writer, chat_hash_id):
        while True:
            message = input('Введите текст сообщения:\r\n')
            writer.write(f'{message}\n\n'.encode())
            await writer.drain()
            print('Ваше сообщение отправлено!')
            logger.info(f'Отправлено сообщение: {message}')
            await receive_response(reader)


    writer.close()



if __name__ == '__main__':
    logging.basicConfig(
        filename='logfile.log',
        filemode='a',
        format='%(levelname)s : %(name)s : %(message)s',
        level=logging.INFO
    )
    env = Env()
    env.read_env()
    chat_hash_id = env.str('CHAT_HASH_ID')
    asyncio.run(handle_writing(chat_hash_id))