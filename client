import os
import platform
import subprocess

import requests
import re

import time

BASE_URL = 'https://login.weixin.qq.com'
QR_PATH = 'qr.jpg'


class client:
    def __init__(self):
        self.browser = requests.session()
        self.uuid = ''

    def login(self):
        self.get_UUID()
        if self.uuid:
            if self.get_QR():
                while True:
                    code = self.check_login()
                    if code == '200':
                        print 'login success'
                        break
                    print code
                    time.sleep(1)

    def get_UUID(self):
        url = '%s/jslogin' % BASE_URL
        param = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
        }
        response = self.browser.get(url, params=param)
        regex = r'window.QRLogin.code = (.{3}); window.QRLogin.uuid = "(.*)";'
        print response.text
        result = re.search(regex, response.text)
        if result and result.group(1) == '200':
            self.uuid = result.group(2)
            return self.uuid

    def get_QR(self):
        url = '%s/qrcode/%s' % (BASE_URL, self.uuid)
        response = self.browser.get(url, stream=True)

        OS = platform.system()
        print OS
        with open(QR_PATH, 'wb') as f:
            f.write(response.content)
        if OS == 'Darwin':
            subprocess.call(['open', QR_PATH])
        elif OS == 'Linux':
            subprocess.call(['xdg-open', QR_PATH])
        else:
            os.startfile(QR_PATH)
        return True

    def check_login(self):
        url = '%s/cgi-bin/mmwebwx-bin/login' % BASE_URL
        param = 'tip=1&uuid=%s&_=%s' % (self.uuid, int(time.time()))
        print url
        response = self.browser.get(url, params=param)
        regex = r'window.code=(\d+)'
        result = re.search(regex, response.text)
        if result and result.group(1) == '200':
            os.remove(QR_PATH)
            return '200'
        elif result:
            return result.group(1)


if __name__ == '__main__':
    c = client()
    c.login()
