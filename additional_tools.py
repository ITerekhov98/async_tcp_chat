import argparse
from environs import Env


def get_config(script_action) -> dict:
    config = {}
    env = Env()
    env.read_env()
    parser = argparse.ArgumentParser(description='Send message to secret chat')
    config['host'] = env.str('HOST', 'minechat.dvmn.org')

    if script_action == 'read':
        config['port'] = env.int('READING_PORT', 5000)
        config['chat_file_path'] = env.str('CHAT_FILE_PATH', 'chat_history.txt')
        parser.add_argument('--chat_file_path')
    else:
        config['port'] = env.int('WRITING_PORT', 5050)
        config['chat_hash_id'] = env.str('CHAT_HASH_ID', 'a')
        parser.add_argument('message')
        parser.add_argument('--chat_hash_id')
        parser.add_argument('--username')

    parser.add_argument('--host')
    parser.add_argument('--port')
    args = parser.parse_args()
    for name, value in vars(args).items():
        if value:
            config[name] = value
    return config
