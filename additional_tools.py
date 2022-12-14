import asyncio
import argparse
from environs import Env
from dataclasses import dataclass


@dataclass
class Queues:
    messages_queue: asyncio.queues.Queue
    saving_queue: asyncio.queues.Queue
    sending_queue: asyncio.queues.Queue
    status_updates_queue: asyncio.queues.Queue
    watchdog_queue: asyncio.queues.Queue


def get_config() -> dict:
    config = {}
    env = Env()
    env.read_env()
    parser = argparse.ArgumentParser(description='Send message to secret chat')
    config['host'] = env.str('HOST', 'minechat.dvmn.org')
    config['reading_port'] = env.int('READING_PORT', 5000)
    config['chat_file_path'] = env.str('CHAT_FILE_PATH', 'chat_history.txt')
    config['writing_port'] = env.int('WRITING_PORT', 5050)
    config['chat_hash_id'] = env.str('CHAT_HASH_ID', 'a')

    parser.add_argument('--chat_file_path')
    parser.add_argument('--chat_hash_id')
    parser.add_argument('--username')

    parser.add_argument('--host')
    parser.add_argument('--reading_port')
    parser.add_argument('--writing_port')

    args = parser.parse_args()
    for name, value in vars(args).items():
        if value:
            config[name] = value
    return config
