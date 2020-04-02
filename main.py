import requests
import time
import telegram
import os
from dotenv import load_dotenv
import logging


#PROXY_FOR_TELEGRAM = 'socks5://96.44.133.110:58690'  # http://spys.one/proxies/

REVIEWS_URL = 'https://dvmn.org/api/user_reviews/'
LONG_POLLING_URL = 'https://dvmn.org/api/long_polling/'
TIMEOUT = 90

MESSAGE_1 = 'Преподаватель проверил работу "{}".\n'
MESSAGE_2 = 'К сожалению, в работе нашлись ошибки.\n\n'
MESSAGE_3 = 'Ошибок нет, можно приступать к следующему уроку.'
MESSAGE_4 = 'Ссылка на урок: https://dvmn.org{}'


def make_dvmn_headers(token):
    dvmn_headers = {
            'Authorization': 'Token {}'.format(token)
        }
    return dvmn_headers


def waiting_for_results(bot, logger, token):
    requested_timestamp = time.time()
    while True:
        try:
            payload = {
                'timestamp': requested_timestamp
            }
            response = requests.get(
                LONG_POLLING_URL,
                headers=make_dvmn_headers(token),
                params=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            devman_answer = response.json()
            if devman_answer['status'] == 'timeout':
                requested_timestamp = devman_answer['timestamp_to_request']
            else:
                requested_timestamp = devman_answer['last_attempt_timestamp']
                lesson_info = devman_answer['new_attempts'][0]
                lesson_title = lesson_info['lesson_title']
                lesson_url = lesson_info['lesson_url']
                lesson_is_negative = lesson_info['is_negative']
                """
                send_notification(
                    bot,
                    lesson_title,
                    lesson_url,
                    lesson_is_negative
                )
                """
                if lesson_is_negative:
                    bot.send_message(
                        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                        text=(MESSAGE_1 + MESSAGE_2 + MESSAGE_4).format(
                            lesson_title,
                            lesson_url
                        )
                    )
                if not lesson_is_negative:
                    bot.send_message(
                        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                        text=(MESSAGE_1 + MESSAGE_3).format(lesson_title)
                    )                

        #except requests.exceptions.ReadTimeout:
        #    pass
        #except requests.ConnectionError:
        #    print('Нет подключения. Ждём...')
        #    time.sleep(3)
        #    continue

        except requests.exceptions.ReadTimeout as err:
            logger.critical(err, exc_info=True)
        except requests.exceptions.ConnectionError as err:
            logger.error(err, exc_info=True)
            time.sleep(1)
        except ConnectionResetError as err:
            logger.error(err, exc_info=True)
            time.sleep(1)
        except requests.exceptions.HTTPError as err:
            logger.error(err, exc_info=True)
            time.sleep(360)
"""
def send_notification(bot, lesson_title, lesson_url, lesson_is_negative):
    if lesson_is_negative:
        bot.send_message(
            chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            text=(MESSAGE_1 + MESSAGE_2 + MESSAGE_4).format(
                lesson_title,
                lesson_url
            )
        )
    if not lesson_is_negative:
        bot.send_message(
            chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            text=(MESSAGE_1 + MESSAGE_3).format(lesson_title)
        )
"""

def main():
    load_dotenv()
    #proxy = telegram.utils.request.Request(proxy_url=PROXY_FOR_TELEGRAM)
    #bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'), request=proxy)
    bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))

    class DVMNBotLogsHandler(logging.Handler):

        def emit(self, record):
            log_entry = self.format(record)
            bot.send_message(
                chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                text=log_entry
            )

    logger = logging.getLogger("DVMNBotLogsHandler")
    logger.setLevel(logging.ERROR)
    logger.addHandler(DVMNBotLogsHandler())
    logging.info('Бот запущен')
    waiting_for_results(bot, logger, os.getenv('DVMN_API_TOKEN'))


if __name__ == '__main__':
    main()
