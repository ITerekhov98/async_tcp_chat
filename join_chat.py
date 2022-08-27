import asyncio
import aiofiles
import datetime

from additional_tools import get_config


async def print_and_save_message(message: str, chat_file_path: str):
    current_time = datetime.datetime.now()
    formated_message = "{} {}".format(
        current_time.strftime('[%d.%m.%y %H:%M]'),
        message
    )
    async with aiofiles.open(chat_file_path, 'a') as f:
        await f.write(formated_message)
    print(formated_message)


async def handle_connection(host: str, port: int, chat_file_path: str):
    reader, writer = await asyncio.open_connection(
        host,
        port
    )
    try:
        while not reader.at_eof():
            message = await reader.readline()
            await print_and_save_message(message.decode(), chat_file_path)
    finally:
        print('Close the connection')
        writer.close()


if __name__ == '__main__':
    config = get_config('read')
    host = config['host']
    port = config['port']
    chat_file_path = config['chat_file_path']
    asyncio.run(handle_connection(host, port, chat_file_path))

