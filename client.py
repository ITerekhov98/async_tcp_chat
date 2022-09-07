import asyncio
import logging
import sys
from anyio import create_task_group
from tkinter import messagebox

from network_tools import (
    HandleReconnect,
    watch_for_connection,
    read_messages,
    handle_writing,
    send_check_message,
    InvalidToken
)
from files_handling import save_messages
from additional_tools import get_config, Queues
from gui import TkAppClosed, draw


RECONNECT_TIMEOUT = 5
ATTEMPTS_TO_RECONNECT = 3
BREAK_DURATION = 60

logger = logging.getLogger('watchdog_logger')


async def handle_connection(
        host: str,
        reading_port: int,
        writing_port: int,
        chat_hash_id: str,
        queues: Queues):
    reconnect = HandleReconnect(ATTEMPTS_TO_RECONNECT, BREAK_DURATION)
    while True:
        try:
            async with create_task_group() as tg:
                tg.start_soon(read_messages, host, reading_port, queues)
                tg.start_soon(
                    watch_for_connection,
                    queues,
                    reconnect,
                    logger,
                    RECONNECT_TIMEOUT
                )
                tg.start_soon(
                    handle_writing,
                    host,
                    writing_port,
                    chat_hash_id,
                    queues
                )
                tg.start_soon(
                    send_check_message,
                    host, 
                    writing_port,
                    queues.watchdog_queue
                )
        except ConnectionError:
            reconnect.attempts_count += 1
            if not reconnect.is_time_to_break():
                logger.warning(
                    f'Attempt {reconnect.attempts_count}'
                    f'of {reconnect.max_attempts}. Reconnecting...'
                )
            else:
                logger.warning(
                    'Limit of reconnecting attempts'
                    f'has been exceeded. Sleep for {BREAK_DURATION}'
                )
                await asyncio.sleep(BREAK_DURATION)


async def main():
    logging.basicConfig(
        filename='logfile.log',
        filemode='a',
        format='%(levelname)s : %(message)s',
        level=logging.INFO
    )
    config = get_config()
    host = config['host']
    reading_port = config['reading_port']
    writing_port = config['writing_port']
    chat_hash_id = config['chat_hash_id']
    chat_filepath = config['chat_file_path']
    queues = Queues(*[asyncio.Queue() for _ in range(5)])

    async with create_task_group() as tg:
        tg.start_soon(draw, queues),
        tg.start_soon(save_messages, chat_filepath, queues)
        tg.start_soon(
            handle_connection,
            host,
            reading_port,
            writing_port,
            chat_hash_id,
            queues
        )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except InvalidToken:
        messagebox.showinfo("Неверный токен", "Проверьте правильность токена")
        sys.exit(1)
    except (KeyboardInterrupt, TkAppClosed):
        sys.exit(0)
