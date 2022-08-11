import requests
from requests.structures import CaseInsensitiveDict
import json
from baseclass import Base


class Telegram:
    def __init__(self):
        self.base = Base()

    def send(self, message, base=None):
        try:
            obj = {
                'botToken': self.base.options['telegram']['botToken'],
                "data": {
                    "text": message,
                    "chat_id": self.base.options['telegram']['chat_id'],
                    "disable_notification": self.base.options['telegram']['disable_notification'],
                }
            }
            url = f"https://api.telegram.org/bot{obj['botToken']}/sendMessage"
            headers = CaseInsensitiveDict()
            headers["Content-Type"] = "application/json"
            post = requests.post(url, headers=headers,
                                 data=json.dumps(obj['data']), timeout=10)
            if (post.status_code == 200):
                return True
            else:
                return False

        except error:
            base.log(f" Telegram error {error}")
            return False


if __name__ == '__main__':
    t = Telegram()
    t.send("salam")
