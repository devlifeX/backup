import requests
from requests.structures import CaseInsensitiveDict
import json
from baseclass import Base


class Telegram:
    def __init__(self):
        self.base = Base()

    def send(self, message, base=None):
        try:
            option = self.base.options['telegram']
            obj = {
                'botToken': option['botToken'],
                "data": {
                    "text": message,
                    "chat_id": option['chat_id'],
                    "disable_notification": option['disable_notification'],
                }
            }
            url = f"https://api.telegram.org/bot{obj['botToken']}/sendMessage"
            headers = CaseInsensitiveDict()
            headers["Content-Type"] = "application/json"

            args = {
                "url": url,
                "headers": headers,
                "data": json.dumps(obj['data']),
                "timeout": 10
            }

            if ('proxy' in option):
                p = option['proxy']
                proxies = {
                    "https": f"https://{p['username']}:{p['password']}@{p['hostname']}:{p['port']}",
                }
                args['proxies'] = proxies

            post = requests.post(**args)
            if (post.status_code == 200):
                return True
            else:
                return False

        except:
            base.log("Error: Send Telegram function")
            return False
