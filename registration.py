import asyncio
import sys
from anyio import create_task_group
import logging

from network_tools import register
from additional_tools import get_config
from gui import draw_success_notice, update_tk, TkAppClosed, draw_register_panel


logger = logging.getLogger('registration')


async def handle_connection(host, port, queue: asyncio.Queue):
    reader, writer = await asyncio.open_connection(host, port)
    username = await queue.get()
    if await register(reader, writer, username):
        await draw_success_notice(username)
        logger.info(f'Successfull registration for {username}')
        raise TkAppClosed()


async def main():
    logging.basicConfig(
        filename='logfile.log',
        filemode='a',
        format='%(levelname)s : %(message)s',
        level=logging.INFO
    )
    config = get_config()
    queue = asyncio.Queue()
    root = await draw_register_panel(queue)

    async with create_task_group() as tg:
        tg.start_soon(update_tk, root)
        tg.start_soon(
            handle_connection,
            config['host'],
            config['writing_port'],
            queue
        )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, TkAppClosed):
        sys.exit(0)



