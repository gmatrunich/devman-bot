import requests
import time
import telegram
import os
from dotenv import load_dotenv


PROXY_FOR_TELEGRAM = 'socks5://3.16.166.191:1080'  # http://spys.one/proxies/

REVIEWS_URL = 'https://dvmn.org/api/user_reviews/'
LONG_POLING_URL = 'https://dvmn.org/api/long_polling/'

MESSAGE_TEMPLATE_1 = 'Преподаватель проверил работу "{}".\n'
MESSAGE_TEMPLATE_2 = 'К сожалению, в работе нашлись ошибки.\n\n'
MESSAGE_TEMPLATE_3 = 'Ошибок нет, можно приступать к следующему уроку.'
MESSAGE_TEMPLATE_4 = 'Ссылка на урок: https://dvmn.org{}'


def make_dvmn_headers(token):
    dvmn_headers = {
            "Authorization": "Token {}".format(token)
        }
    return dvmn_headers


def waiting_for_results(token):
    requested_timestamp = ''
    while True:
        try:
            payload = {
                'timestamp': requested_timestamp
            }
            response = requests.get(LONG_POLING_URL, headers=make_dvmn_headers(token), params=payload)
            response.raise_for_status()
            devman_answer = response.json()
            if devman_answer['status'] == 'found':
                requested_timestamp = devman_answer['last_attempt_timestamp']
                lesson_title = devman_answer['new_attempts'][0]['lesson_title']
                lesson_url = devman_answer['new_attempts'][0]['lesson_url']
                lesson_is_negative = devman_answer['new_attempts'][0]['is_negative']
                send_notification(lesson_title, lesson_url, lesson_is_negative)
            else:
                requested_timestamp = devman_answer['timestamp_to_request']
        except requests.exceptions.ReadTimeout:
            print("Ошибка: время вышло")
            continue
        except requests.ConnectionError:
            print("Нет подключения. Ждём...")
            time.sleep(3)
            continue


def send_notification(lesson_title, lesson_url, lesson_is_negative):
    if lesson_is_negative is True:
        bot.send_message(chat_id=os.getenv("TELEGRAM_CHAT_ID"), text=(MESSAGE_TEMPLATE_1 + MESSAGE_TEMPLATE_2 + MESSAGE_TEMPLATE_4).format(lesson_title, lesson_url))
    if lesson_is_negative is False:
        bot.send_message(chat_id=os.getenv("TELEGRAM_CHAT_ID"), text=(MESSAGE_TEMPLATE_1 + MESSAGE_TEMPLATE_3).format(lesson_title))


if __name__ == '__main__':
    load_dotenv()
    proxy = telegram.utils.request.Request(proxy_url=PROXY_FOR_TELEGRAM)
    bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), request=proxy)
    waiting_for_results(os.getenv("DVMN_API_TOKEN"))
