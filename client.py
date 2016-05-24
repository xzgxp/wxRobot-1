# coding=utf-8
import json
import os
import platform
import re
import subprocess
import time
import requests
import xml.etree.ElementTree as ET

BASE_URL = 'https://login.weixin.qq.com'
QR_PATH = 'qr.jpg'


class client:
    def __init__(self):
        self.browser = requests.session()
        self.uuid = ''
        self.wxInfo = {}

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
                self.wx_Init()

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
            # todo 无法自动关闭程序
            os.startfile(QR_PATH)
        return True

    def check_login(self):
        url = '%s/cgi-bin/mmwebwx-bin/login' % BASE_URL
        param = 'tip=1&uuid=%s&_=%s' % (self.uuid, int(time.time()))
        response = self.browser.get(url, params=param)
        regex = r'window.code=(\d+)'
        result = re.search(regex, response.text)
        if result and result.group(1) == '200':
            os.remove(QR_PATH)
            regex = r'window.redirect_uri="(.*)"'
            result = re.search(regex, response.text)
            self.wxInfo['url'] = result.group(1)[:result.group(1).rfind('/')]
            self.wxInfo['BaseRequest'] = {}
            response = self.browser.get(result.group(1), allow_redirects=False)
            root = ET.fromstring(response.text)
            for element in root:
                if element.tag == 'skey' or element.tag == 'wxsid' or element.tag == 'wxuin' or element.tag == 'pass_ticket':
                    self.wxInfo['BaseRequest'][element.tag] = element.text
            return '200'
        elif result:
            return result.group(1)

    def wx_Init(self):
        url = '%s/webwxinit?r=%s' % (self.wxInfo['url'], int(time.time()))
        data = {
            'BaseRequest': self.wxInfo['BaseRequest']
        }
        headers = {'ContentType': 'application/json; charset=UTF-8'}
        response = self.browser.post(url, data=json.dumps(data), headers=headers)
        print response.content


if __name__ == '__main__':
    c = client()
    c.login()
