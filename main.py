import asyncio
import aiofiles
import datetime


async def print_and_save_message(message: str, chat_file='chat_history.txt'):
    current_time = datetime.datetime.now()
    formated_message = "{} {}".format(
        current_time.strftime('[%d.%m.%y %H:%M]'),
        message
    )
    async with aiofiles.open(chat_file, 'a') as f:
        await f.write(formated_message)
    print(formated_message)


async def main():
    reader, writer = await asyncio.open_connection(
        'minechat.dvmn.org', 5000)

    while not reader.at_eof():
        message = await reader.readline()

        await print_and_save_message(message.decode())

    print('Close the connection')
    writer.close()

asyncio.run(main())
