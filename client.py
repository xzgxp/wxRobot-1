# coding=utf-8
import json
import os
import platform
import re
import subprocess
import time
import requests
import xml.etree.ElementTree as ET
import display

import thread

BASE_URL = 'https://login.weixin.qq.com'
QR_PATH = 'qr.jpg'


class client:
    def __init__(self):
        self.browser = requests.session()
        self.uuid = ''
        self.wxInfo = {}  # 登陆相关信息
        self.User = {}  # 当前用户信息
        self.Contact = []  # 用户联系人

    def login(self):
        self.get_UUID()
        if self.uuid:
            if self.get_QR():
                while True:
                    code = self.check_login()
                    if code == '200':
                        print 'login success'
                        break
                    time.sleep(1)
                self.wx_Init()
        self.wx_StatusNotify()
        self.wx_GetContact()
        self.wx_Start()

    def get_UUID(self):
        display.print_line('获取UUID')
        url = '%s/jslogin' % BASE_URL
        param = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
        }
        response = self.browser.get(url, params=param)
        regex = r'window.QRLogin.code = (.{3}); window.QRLogin.uuid = "(.*)";'
        # print response.text
        result = re.search(regex, response.text)
        if result and result.group(1) == '200':
            self.uuid = result.group(2)
            return self.uuid

    def get_QR(self):
        url = '%s/qrcode/%s' % (BASE_URL, self.uuid)
        response = self.browser.get(url, stream=True)

        OS = platform.system()
        # print OS
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
        result = json.loads(response.content)
        self.User = result['User']
        self.wxInfo['SyncKey'] = '|'.join(['%s_%s' % (item['Key'], item['Val']) for item in result['SyncKey']['List']])

    def wx_StatusNotify(self):
        url = '%s/webwxstatusnotify' % self.wxInfo['url']
        data = {
            'BaseRequest': self.wxInfo['BaseRequest'],
            'Code': 3,
            'FromUserName': self.User['UserName'],
            'ToUserName': self.User['UserName'],
            'ClientMsgId': int(time.time())
        }
        headers = {'ContentType': 'application/json; charset=UTF-8'}
        self.browser.post(url, json.dumps(data), headers=headers)

    def wx_GetContact(self):
        url = '%s/webwxgetcontact?r=%s&seq=0&skey=%s' % (self.wxInfo['url'],
                                                         int(time.time()), self.wxInfo['BaseRequest']['skey'])
        headers = {'ContentType': 'application/json; charset=UTF-8'}
        r = self.browser.get(url, headers=headers)
        self.Contact = json.loads(r.content.decode('utf-8', 'replace'))['MemberList']

    def msg_Check(self):
        display.print_line('检验是否有消息')
        url = '%s/synccheck' % self.wxInfo['url']
        params = {
            'r': int(time.time()),
            'skey': self.wxInfo['BaseRequest']['skey'],
            'sid': self.wxInfo['BaseRequest']['wxsid'],
            'uin': self.wxInfo['BaseRequest']['wxuin'],
            'deviceid': self.wxInfo['BaseRequest']['pass_ticket'],
            'synckey': self.wxInfo['SyncKey']
        }
        result = self.browser.get(url, params=params)
        regex = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
        pm = re.search(regex, result.text)
        if pm.group(1) != '0':
            print '同步消息失败!'
            return None
        # print '获取消息:' + result.text.decode('utf-8', 'replace')
        return pm.group(2)

    def msg_Get(self):
        url = '%s/webwxsync?sid=%s&skey=%s' % (
            self.wxInfo['url'], self.wxInfo['BaseRequest']['wxsid'], self.wxInfo['BaseRequest']['skey'])
        data = {
            'BaseRequest': self.wxInfo['BaseRequest'],
            'SyncKey': self.wxInfo['SyncKey'],
            'rr': int(time.time())
        }
        headers = {'ContentType': 'application/json; charset=UTF-8'}
        r = self.browser.post(url, data=json.dumps(data), headers=headers)

        dic = json.loads(r.content.decode('utf-8', 'replace'))
        self.wxInfo['SyncKey'] = dic['SyncKey']
        if dic['AddMsgCount'] != 0:
            return dic['AddMsgList']

    def wx_Start(self):
        def maintain_loop():
            i = self.msg_Check()
            count = 0  # 错误次数
            pauseTime = 1
            while i and count < 4:
                try:
                    if pauseTime < 5:
                        pauseTime += 2
                    if i != '0':
                        msgList = self.msg_Get()
                        print msgList
                    if msgList:
                        # msgList = self.__produce_msg(msgList)
                        # for msg in msgList: self.msgList.insert(0, msg)
                        pauseTime = 1
                    time.sleep(pauseTime)
                    i = self.msg_Check()
                    count = 0
                except Exception, e:
                    print e.message
                    count += 1
                    time.sleep(count * 3)

        maintain_loop()


if __name__ == '__main__':
    c = client()
    c.login()
