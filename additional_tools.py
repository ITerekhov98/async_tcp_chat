import argparse
from environs import Env, EnvError


def get_config(script_action) -> dict:
    config = {}
    env = Env()
    env.read_env()
    parser = argparse.ArgumentParser(description='Send message to secret chat')
    config['host'] = env.str('HOST', None)
    config['port'] = env.int('WRITING_PORT', 0)
    if script_action == 'read':
        config['chat_file_path'] = env.str('chat_file_path', 'chat_history.txt')
        parser.add_argument('--chat_file_path')
    else:
        config['chat_hash_id'] = env.str('CHAT_HASH_ID', None)
        parser.add_argument('message')
        parser.add_argument('--chat_hash_id')
        parser.add_argument('--username')
    
    parser.add_argument('--host')
    parser.add_argument('--port')
    args = parser.parse_args()
    for name, value in vars(args).items():
        if value:
            config[name] = value
    if not config['host'] or not config['port']:
        raise EnvError('Не указаны данные для подключения!')
    return config