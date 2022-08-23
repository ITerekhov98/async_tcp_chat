import asyncio
from environs import Env

async def handle_writing(chat_hash_id):
    reader, writer = await asyncio.open_connection(
        'minechat.dvmn.org', 5050)

    response = await reader.readline()
    response = response.decode()
    if response.startswith('Hello'):
        writer.write(f'{chat_hash_id}\n'.encode())

    while True:
        message = input('Введите текст сообщения:\r\n')
        writer.write(f'{message}\n\n'.encode())
        await writer.drain()
        print('Ваше сообщение отправлено!')

    writer.close()



if __name__ == '__main__':
    env = Env()
    env.read_env()
    chat_hash_id = env.str('CHAT_HASH_ID')
    asyncio.run(handle_writing(chat_hash_id))