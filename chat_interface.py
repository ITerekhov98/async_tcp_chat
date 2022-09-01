import time
import tkinter as tk
import asyncio
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox

from additional_tools import get_config
from join_chat import read_messages, save_messages, ReadConnectionStateChanged
import logging
from anyio import sleep, create_task_group, run
from async_timeout import timeout
from write_to_chat import handle_writing, InvalidToken, SendingConnectionStateChanged, NicknameReceived

logger = logging.getLogger('watchdog_logger')


RECONNECT_TIMEOUT = 5
ATTEMPTS_TO_RECONNECT = 3
BREAK_DURATION = 60

class TkAppClosed(Exception):
    pass


class HandleReconnect():
    def __init__(self, max_attempts, time_to_break):
        self.max_attempts = max_attempts
        self.time_to_break = time_to_break
        self.attempts_count = 0
    
    def is_time_to_break(self):
        return self.max_attempts <= self.attempts_count

    def reset_attempts(self):
        self.attempts_count = 0


def process_new_message(input_field, sending_queue):
    text = input_field.get()
    sending_queue.put_nowait(text)
    input_field.delete(0, tk.END)


async def update_tk(root_frame, interval=1 / 120):
    while True:
        try:
            root_frame.update()
        except tk.TclError:
            # if application has been destroyed/closed
            raise TkAppClosed()
        await asyncio.sleep(interval)


async def update_conversation_history(panel, messages_queue):
    while True:
        msg = await messages_queue.get()

        panel['state'] = 'normal'
        if panel.index('end-1c') != '1.0':
            panel.insert('end', '\n')
        panel.insert('end', msg)
        # TODO сделать промотку умной, чтобы не мешала просматривать историю сообщений
        # ScrolledText.frame
        # ScrolledText.vbar
        panel.yview(tk.END)
        panel['state'] = 'disabled'


async def update_status_panel(status_labels, status_updates_queue):
    nickname_label, read_label, write_label = status_labels

    read_label['text'] = f'Чтение: нет соединения'
    write_label['text'] = f'Отправка: нет соединения'
    nickname_label['text'] = f'Имя пользователя: неизвестно'

    while True:
        msg = await status_updates_queue.get()
        if isinstance(msg, ReadConnectionStateChanged):
            read_label['text'] = f'Чтение: {msg}'

        if isinstance(msg, SendingConnectionStateChanged):
            write_label['text'] = f'Отправка: {msg}'

        if isinstance(msg, NicknameReceived):
            nickname_label['text'] = f'Имя пользователя: {msg.nickname}'


def create_status_panel(root_frame):
    status_frame = tk.Frame(root_frame)
    status_frame.pack(side="bottom", fill=tk.X)

    connections_frame = tk.Frame(status_frame)
    connections_frame.pack(side="left")

    nickname_label = tk.Label(connections_frame, height=1, fg='grey', font='arial 10', anchor='w')
    nickname_label.pack(side="top", fill=tk.X)

    status_read_label = tk.Label(connections_frame, height=1, fg='grey', font='arial 10', anchor='w')
    status_read_label.pack(side="top", fill=tk.X)

    status_write_label = tk.Label(connections_frame, height=1, fg='grey', font='arial 10', anchor='w')
    status_write_label.pack(side="top", fill=tk.X)

    return (nickname_label, status_read_label, status_write_label)


async def draw(messages_queue, sending_queue, status_updates_queue):
    root = tk.Tk()

    root.title('Чат Майнкрафтера')

    root_frame = tk.Frame()
    root_frame.pack(fill="both", expand=True)

    status_labels = create_status_panel(root_frame)

    input_frame = tk.Frame(root_frame)
    input_frame.pack(side="bottom", fill=tk.X)

    input_field = tk.Entry(input_frame)
    input_field.pack(side="left", fill=tk.X, expand=True)

    input_field.bind("<Return>", lambda event: process_new_message(input_field, sending_queue))

    send_button = tk.Button(input_frame)
    send_button["text"] = "Отправить"
    send_button["command"] = lambda: process_new_message(input_field, sending_queue)
    send_button.pack(side="left")

    conversation_panel = ScrolledText(root_frame, wrap='none')
    conversation_panel.pack(side="top", fill="both", expand=True)

    async with create_task_group() as tg:
        tg.start_soon(update_tk, root_frame),
        tg.start_soon(update_conversation_history, conversation_panel, messages_queue),
        tg.start_soon(update_status_panel, status_labels, status_updates_queue)



async def watch_for_connection(watchdog_queue: asyncio.Queue, reconnect: HandleReconnect):
    while True:
        try:
            async with timeout(RECONNECT_TIMEOUT):
                notice = await watchdog_queue.get()
            reconnect.reset_attempts()
            logger.info(f'[{time.time()}] {notice}')
        except asyncio.exceptions.TimeoutError:
            raise ConnectionError
        


async def handle_connection(host, reading_port, writing_port, messages_queue, saving_queue, status_updates_queue, chat_hash_id, sending_queue, watchdog_queue: asyncio.Queue):
    reconnect = HandleReconnect(ATTEMPTS_TO_RECONNECT, BREAK_DURATION)
    while True:
        try:
            async with create_task_group() as tg:
                tg.start_soon(watch_for_connection, watchdog_queue, reconnect)
                tg.start_soon(read_messages, host, reading_port, messages_queue, saving_queue, status_updates_queue, watchdog_queue)
                tg.start_soon(handle_writing, host, writing_port, chat_hash_id, sending_queue, status_updates_queue, watchdog_queue)
        except ConnectionError:
            reconnect.attempts_count += 1
            if not reconnect.is_time_to_break():
                logger.warning(f'Attempt {reconnect.attempts_count} of {reconnect.max_attempts}. Reconnecting...')
            else:
                logger.warning(f'Limit of reconnecting attempts has been exceeded. Sleep for {BREAK_DURATION}')
                await asyncio.sleep(BREAK_DURATION)


async def main():
    logging.basicConfig(
        filename='logfile.log',
        filemode='a',
        format='%(levelname)s : %(message)s',
        level=logging.INFO
    )
    config = get_config('read')
    host = config['host']
    reading_port = config['reading_port']
    writing_port = config['writing_port']
    chat_hash_id = config['chat_hash_id']
    messages_queue = asyncio.Queue()
    saving_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()
    try:
        async with create_task_group() as tg:
            tg.start_soon(draw, messages_queue, sending_queue, status_updates_queue),
            tg.start_soon(save_messages, 'chat_history.txt', saving_queue, messages_queue)
            tg.start_soon(handle_connection, host, reading_port, writing_port, messages_queue, saving_queue, status_updates_queue, chat_hash_id, sending_queue, watchdog_queue)
    except InvalidToken:
        messagebox.showinfo("Неверный токен", "Проверьте правильность токена")

asyncio.run(main())