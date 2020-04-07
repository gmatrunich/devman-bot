import requests
import time
import telegram
import os
from dotenv import load_dotenv
import logging


logger = logging.getLogger("DVMNBotLogsHandler")


REVIEWS_URL = 'https://dvmn.org/api/user_reviews/'
LONG_POLLING_URL = 'https://dvmn.org/api/long_polling/'
TIMEOUT = 90

LESSON_WITH_ERRORS = '''Преподаватель проверил работу "{}".
К сожалению, в работе нашлись ошибки.
Ссылка на урок: https://dvmn.org{}
'''
LESSON_WITHOUT_ERRORS = '''Преподаватель проверил работу "{}".
Ошибок нет, можно приступать к следующему уроку.'''


def waiting_for_results(bot, token):
    requested_timestamp = time.time()
    while True:
        try:
            dvmn_headers = {
                        'Authorization': 'Token {}'.format(token)
                    }
            payload = {
                'timestamp': requested_timestamp
            }
            response = requests.get(
                LONG_POLLING_URL,
                headers=dvmn_headers,
                params=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            devman_answer = response.json()
            if devman_answer['status'] == 'timeout':
                requested_timestamp = devman_answer['timestamp_to_request']
            else:
                requested_timestamp = devman_answer['last_attempt_timestamp']
                lesson_details = devman_answer['new_attempts'][0]
                lesson_title = lesson_details['lesson_title']
                lesson_url = lesson_details['lesson_url']
                lesson_is_negative = lesson_details['is_negative']
                if lesson_is_negative:
                    bot.send_message(
                        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                        text=(
                            LESSON_WITH_ERRORS
                        ).format(
                            lesson_title,
                            lesson_url
                        )
                    )
                if not lesson_is_negative:
                    bot.send_message(
                        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                        text=(
                            LESSON_WITHOUT_ERRORS
                        ).format(lesson_title)
                    )
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectionError as er:
            logger.error(er, exc_info=True)
            time.sleep(3)
            continue
        except ConnectionResetError as er:
            logger.error(er, exc_info=True)
            time.sleep(3)
        except requests.exceptions.HTTPError as er:
            logger.error(er, exc_info=True)
            time.sleep(60)


def send_messages():
    lesson_title = "Запускаем бота на сервере"
    lesson_url = "https://dvmn.org/modules/chat-bots/lesson/bot-deploy/"
    bot.send_message(
        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        text=(
            LESSON_WITH_ERRORS
        ).format(
            lesson_title,
            lesson_url
        )
    )
    bot.send_message(
        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        text=(
            LESSON_WITHOUT_ERRORS
        ).format(lesson_title)
    )


def main():
    load_dotenv()
    bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))

    class DVMNBotLogsHandler(logging.Handler):

        def emit(self, record):
            log_entry = self.format(record)
            bot.send_message(
                chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                text=log_entry
            )

    logger.setLevel(logging.DEBUG)
    logger.addHandler(DVMNBotLogsHandler())
    logger.info('Бот запущен')
    #waiting_for_results(bot, os.getenv('DVMN_API_TOKEN'))
    send_messages(bot, os.getenv('DVMN_API_TOKEN'))


if __name__ == '__main__':
    main()
