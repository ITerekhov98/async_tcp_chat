## Чтение и отправка сообщений в чат с помощью Asyncio Streams

## Установка
Скачайте репозиторий с кодом, установите необходимые зависимости:
```
pip install -r requirements.txt
```

## Запуск
Для работы скрипта необходимо указать хост и порт сервера с чатом. Это можно сделать с помощью *.env* файла:
```
HOST=your_hostname
PORT=your_port
```
Также можно их указать с помощью аргументов командной строки: --host, --port.

### Чтение сообщений чата

Выполните в консоли команду:
```
python join_chat.py
```
Все поступающие сообщения будут выводиться в консоль, а также дублироваться в файл (по умолчанию chat_history.txt).

### Отправка сообщений в чат

Выполните в консоли команду:
```
python write_to_chat.py message 
```
Обратите внимание, что message здесь это обязательный аргумент, текст вашего сообщения. Если вы отправляете сообщение впервые, программа предложит вам зарегистрироваться и указать никнейм.
После регистрации программа сохранит ваш полученный hash_id и в дальнейшем будет авторизовываться с помощью него.

### Настройка
Помимо упомянутых выше обязательных параметров host и port есть несколько опциональных:
- Путь к файлу, в котором будет сохраняться история переписки (актуален для сркипта с чтением чата): 
  + `CHAT_FILE_PATH` для *.env*
  + `--chat_file_path` для cli
- Ваш hash_id, полученный при регистрации (актуален для отправки сообщения):
  + `CHAT_HASH_ID` для *.env*
  + `--chat_hash_id` для cli
- Ваш username. Можно указать для смены никнейма (актуален для сркипта с чтением чата):
  + `--username` для cli

