import asyncio
import aiofiles
import datetime
import argparse
from environs import Env


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
        host, port)

    while not reader.at_eof():
        message = await reader.readline()

        await print_and_save_message(message.decode(), chat_file_path)

    print('Close the connection')
    writer.close()


def get_config() -> dict:
    config = {}
    env = Env()
    env.read_env()
    config['host'] = env.str('host', 'minechat.dvmn.org')
    config['port'] = env.int('port', 5000)
    config['chat_file_path'] = env.str('chat_file_path', 'chat_history.txt')
    parser = argparse.ArgumentParser(description='Connect to secret chat')
    parser.add_argument('--host')
    parser.add_argument('--port')
    parser.add_argument('--chat_file_path')
    args = parser.parse_args()
    for name, value in vars(args).items():
        if value:
            config[name] = value
    return config


if __name__ == '__main__':
    config = get_config()
    asyncio.run(handle_connection(**config))

