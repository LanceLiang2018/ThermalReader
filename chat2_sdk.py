import requests
import json
import base64
import threading
import time
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtCore import *
from PyQt5 import sip
import sys
# import win32api
# import win32con
from PIL import Image
import numpy as np
import io
import os
# from imageProcessing import image_process


class Chat2Comm:
    def __init__(self, server_choose=1):
        # self.servers = ["http://lance-chatroom2.herokuapp.com/v3/api",
        #                 "http://127.0.0.1:5000/v3/api"]
        self.servers = ["http://lance-latina-debug.herokuapp.com/v3/api",
                        "http://127.0.0.1:5000/v3/api"]
        self.SERVER = self.servers[server_choose]
        self.MAIN = ""
        self.ABOUT = "about"
        self.BEAT = "beat"
        self.LOGIN = "login"
        self.SIGNUP = "signup"
        self.GET_MESSAGES = "get_messages"
        self.SEND_MESSAGE = "send_message"
        self.GET_HEAD = "get_head"
        self.CLEAR_ALL = "clear_all"
        self.SET_USER = "set_user"
        self.JOIN_IN = "join_in"
        self.CREATE_ROOM = "create_room"
        self.SET_ROOM = "set_room"
        self.GET_ROOM = "get_room"
        self.GET_ROOM_ALL = "get_room_all"
        self.GET_ROOM_INFO = "get_room_info"
        self.SET_ROOM_INFO = "set_room_info"
        self.UPLOAD = "upload"
        self.MAKE_FRIENDS = "make_friends"

        self.UID = 'uid'
        self.MID = 'mid'
        self.GID = 'gid'
        self.AUTH = 'auth'
        self.MESSAGE_TYPE = 'message_type'
        self.USERNAME = 'username'
        self.PASSWORD = 'password'
        self.EMAIL = 'email'
        self.NAME = 'name'

    # 异步post请求
    # v2
    def post_(self, url: str, params: dict, callback):
        def post_request(murl: str, mparams: dict, mcallback):
            mcallback(requests.post(murl, data=mparams))
        t = threading.Thread(target=post_request, args=(url, params, callback))
        # t.setDaemon(True)
        t.start()

    # v3
    def post(self, action: str, params: dict):
        params['action'] = action
        r = requests.post(self.SERVER, data=params)
        if r.status_code != 200:
            return {'code': '-1', 'message': "Server Error."}
        return r.json()

    # v2
    def get(self, url: str):
        r = requests.get(url)
        if r.status_code != 200:
            return {'code': '-1', 'message': "Server Error."}
        return r.json()

    # 异步get请求
    # v2
    def get_(self, url: str, callback):
        def post_request(murl: str, mcallback):
            mcallback(requests.get(murl))
        t = threading.Thread(target=post_request, args=(url, callback))
        # t.setDaemon(True)
        t.start()


class Chat2Client:
    def __init__(self, server_choose=1):
        self.comm = Chat2Comm(server_choose=server_choose)
        self.username = ""
        self.auth = ""
        self.gid = 0
        self.latest_mid = 0
        self.load()

    def init(self):
        self.username = ""
        self.auth = ""
        self.gid = 0
        self.latest_mid = 0
        self.save()

    def save(self):
        with open('save.json', 'w') as f:
            f.write(json.dumps({
                'username': self.username,
                'auth': self.auth,
                'latest_mid': self.latest_mid}))

    def load(self):
        try:
            with open('save.json', 'r') as f:
                settings = json.load(f)
                self.username = settings['username']
                self.auth = settings['auth']
                self.latest_mid = settings['latest_mid']
        except Exception as e:
            print(e)

    def parse_errors(self, result):
        print(result['message'])

    def post_auth(self, action: str, params: dict):
        params['auth'] = self.auth
        return self.comm.post(action, params)

    def login_(self, username, password):
        def login_callback(request):
            result = json.loads(request.text)
            if result['code'] != '0':
                self.parse_errors(result)
                return int(result['code'])
            self.auth = result['data']['auth']
            self.username = username
        self.comm.post_(self.comm.LOGIN, {'username': username, 'password': password}, login_callback)
        return

    def login(self, username, password):
        result = self.post_auth(self.comm.LOGIN, {'username': username, 'password': password})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        self.username = username
        self.auth = result['data']['user_info']['auth']
        return int(result['code'])

    def signup(self, username, password, email='LanceLiang2018@163.com', name='Lance', user_type='printer'):
        result = self.post_auth(self.comm.SIGNUP,
                                {'username': username, 'password': password,
                                 'email': email, 'name': name, 'user_type': user_type})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        return int(result['code'])

    def logout(self):
        self.auth = ''

    def beat(self):
        result = self.post_auth(self.comm.BEAT, {})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        return int(result['code'])

    def create_room(self, room_name):
        result = self.post_auth(self.comm.CREATE_ROOM, {'name': room_name})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        return int(result['code'])

    def get_rooms(self):
        result = self.post_auth(self.comm.GET_ROOM_ALL, {})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        return result['data']['room_data']

    def enter_room(self, gid: int):
        self.gid = gid

    def quit_room(self):
        self.gid = 0

    def get_messages(self, gid: int=0):
        # must init gid to get single room messages
        if gid == 0:
            gid = self.gid
        result = self.post_auth(self.comm.GET_MESSAGES, {'since': self.latest_mid, 'gid': gid})
        if result['code'] != '0':
            self.parse_errors(result)
            return
        messages = result['data']['message']
        for m in messages:
            self.latest_mid = max(self.latest_mid, m['mid'])
            # print("\t\tlatest_mid:", self.latest_mid)
        self.save()
        return messages

    def send_message(self, text: str, message_type='text', gid=0):
        if gid == 0:
            gid = self.gid
        result = self.post_auth(self.comm.SEND_MESSAGE,
                                {'message_type': message_type, 'text': text, 'gid': gid})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        return int(result['code'])

    def upload(self, filename, data):
        result = self.post_auth(self.comm.UPLOAD, {'data': data, 'filename': filename})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        return result['data']['upload_result']

    def clear_all(self):
        # result = self.post_auth(self.comm.CLEAR_ALL, {})
        result = self.comm.get(self.comm.SERVER + '/clear_all')
        print('Clear_ALL:', result)
        return int(result['code'])

    def make_friends(self, friend: str):
        result = self.post_auth(self.comm.MAKE_FRIENDS, {'friend': friend})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        return int(result['code'])

    def join_in(self, gid: int):
        result = self.post_auth(self.comm.JOIN_IN, {'gid': str(gid)})
        if result['code'] != '0':
            self.parse_errors(result)
            return int(result['code'])
        return int(result['code'])

    def get_image(self, url):
        content = requests.get(url).content
        stream = io.BytesIO(content)
        image = Image.open(stream)
        return image

'''
def delay_enter():
    time.sleep(0.5)
    win32api.keybd_event(0x0D, 0, 0, 0)  # Enter
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放按键
'''


class TextPrinterWindow(QMainWindow):
    def __init__(self, parent=None, text=None, paper_type='58'):
        super(TextPrinterWindow, self).__init__(parent)

        printer = QPrinter()
        # printer.setOutputFormat(QPrinter.PdfFormat)
        # printer.setOutputFileName("pdf.pdf")

        # rect = QRectF(0, 0, 180, 3276)
        if paper_type == 'A4':
            width = printer.logicalDpiX() * (210 / 25.4)
            height = printer.logicalDpiY() * (297 / 25.4)
            rect = QRectF(0, 0, width, height)
        else:
            width = 180
            height = 3276
            rect = QRectF(0, 0, width, height)

        option = QTextOption(Qt.AlignLeft)
        option.setWrapMode(QTextOption.WordWrap)

        painter = QPainter()
        printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.begin(printer)
        if text is not None:
            painter.drawText(rect, text, option)
        painter.end()


class ImagePrinterWindow(QMainWindow):
    def __init__(self, parent=None, image=None, paper_type='58'):
        super(ImagePrinterWindow, self).__init__(parent)

        printer = QPrinter()
        # printer.setOutputFormat(QPrinter.PdfFormat)
        # printer.setOutputFileName("pdf.pdf")

        option = QTextOption(Qt.AlignLeft)
        option.setWrapMode(QTextOption.WordWrap)

        painter = QPainter()
        printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.begin(printer)
        if image is not None:
            # image = QImage(image)
            # image = Image.open(image)
            if image.size[1] < image.size[0]:
                image = image.rotate(90, expand=True)
            if paper_type == 'A4':
                width = printer.logicalDpiX() * (210 / 25.4)
                height = printer.logicalDpiY() * (297 / 25.4)
                if width / height < image.size[0] / image.size[1]:
                    rect = QRectF(0, 0, width, image.size[1] * (width / image.size[0]))
                else:
                    rect = QRectF(0, 0, image.size[0] * (height / image.size[1]), height)
            else:
                width = 180
                rect = QRectF(0, 0, width, image.size[1] * (width / image.size[0]))
            img = np.array(image)
            im = QImage(img[:], img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
            painter.drawImage(rect, im)
        painter.end()


class Chat2Printer:
    def print_text(self, text, paper_type='58'):
        global app
        window = TextPrinterWindow(text=text)
        app.closeAllWindows()

    def print_image(self, image, paper_type='58'):
        global app
        window = ImagePrinterWindow(image=image, paper_type=paper_type)
        app.closeAllWindows()


def module_test():
    client = Chat2Client(server_choose=0)
    client.init()
    # client.clear_all()
    client.signup('Lance', '')
    client.login('Lance', '')
    # time.sleep(1)
    print(client.username, client.auth)
    client.create_room('NameLose')
    rooms = client.get_rooms()
    print(rooms)
    client.enter_room(rooms[0]['gid'])
    messages = client.get_new_message()
    print(len(messages), messages)
    messages = client.get_new_message()
    print(len(messages), messages)
    client.send_message('First commit~')
    messages = client.get_new_message()
    print(len(messages), messages)

    with open('save.json', 'rb') as f:
        data = f.read()
        b64 = base64.b64encode(data)
        upload_result = client.upload('save.json', b64)
        print(upload_result)

    client.send_message(upload_result['url'], message_type='file')
    messages = client.get_new_message()
    print(len(messages), messages)


def mini_test():
    client = Chat2Client()

    client.login('Lance', '')
    print(client.username, client.auth)
    rooms = client.get_rooms()
    print(rooms)
    client.enter_room(rooms[0]['gid'])

    while True:
        messages = client.get_new_message()
        print(len(messages), messages)
        for m in messages:
            client.send_message('我反对 @%s的观点！' % m['username'])
            client.latest_mid = client.latest_mid + 1
            client.save()
        time.sleep(10)



def friend_test():
    client = Chat2Client(server_choose=0)
    client.login('Tony', '')
    rooms = client.get_rooms()
    print(rooms)
    # client.join_in(2)
    # client.make_friends('Lance')
    # rooms = client.get_rooms()
    # print(rooms)
    client.enter_room(4)
    try:
        while True:
            messages = client.get_new_message()
            # print(messages)
            for m in messages:
                if m['username'] == client.username:
                    continue
                print(m)
                if m['type'] == 'image':
                    image = client.get_image(m['text'])
                    printer = Chat2Printer()
                    printer.print_image(image=image)
                if m['type'] == 'text':
                    text = "@{username}\n{text}".format(username=m['username'], text=m['text'])
                    printer = Chat2Printer()
                    printer.print_text(text=text)
                # time.sleep(1)
            # time.sleep(10)
    except Exception as e:
        print(e)
        return


class LatinaPrinter:
    def __init__(self):
        global app
        global default_font
        app.setFont(default_font)

        self.default_option = {}

        self.scenery_option = {
            'black_white': True,
            'intensity': True,
            'high_enhance': True,
        }

        self.comic_option = {
            'black_white': True,
        }

        self.black_white_option = {
            'black_white': True,
        }

        self.options = {}
        self.print_options = {
            'comic': self.comic_option,
            'default': self.default_option,
            'black_white': self.black_white_option
        }
        self.font_options = {}
        self.default_font_option = {
            'font-family': '微软雅黑',
            'font-size': 10,
        }
        self.sdk_running = False
        self.quit_confirm = False
        self.font_families = ['微软雅黑', '宋体', '仿宋', '黑体',
                              'Microsoft YaHei Mono', '幼圆', '楷体', '隶书']

        self.client = Chat2Client(server_choose=0)
        self.load()

    def save(self):
        with open('options.json', 'w') as f:
            f.write(json.dumps({
                'options': self.options,
                'font_options': self.font_options
            }))

    def load(self):
        try:
            with open('options.json', 'r') as f:
                save_options = json.load(f)
                self.options = save_options['options']
                self.font_options = save_options['font_options']
        except Exception as e:
            print(e, 'try to save...')
            self.save()

    def set_option(self, username: str, option: str):
        if option not in self.print_options:
            return '修改设置失败！'
        self.options[username] = self.print_options[option]
        self.save()
        return '修改设置成功！'

    def set_font_option(self, username: str, size: int=None, family: str=None):
        if family is not None and family not in self.font_families:
            return '修改设置失败！'
        if size is not None and size > 30:
            return '修改设置失败！'
        option = self.default_font_option
        if family is not None:
            option['font-family'] = family
        if size is not None:
            option['font-size'] = size
        self.font_options[username] = option
        self.save()
        return '修改设置成功！'

    def mainloop(self, username='Printer', password='1352040930lxr'):
        global app
        global default_font
        self.client.logout()
        code = self.client.login(username, password)
        if code != 0:
            print("新用户，注册...")
            code = self.client.signup(username=username, password=password, user_type='printer')
            if code != 0:
                print("注册错误...", code)
                return
            code = self.client.login(username, password)
        rooms = self.client.get_rooms()
        print(rooms)
        # client.join_in(2)
        # client.make_friends('Lance')
        # rooms = client.get_rooms()
        # print(rooms)
        # self.client.enter_room(10)
        self.client.quit_room()
        self.sdk_running = True
        while True:
            if self.sdk_running is False:
                self.quit_confirm = True
                print("latina quit.")
                self.quit()
                quit()
            try:
                # messages = self.client.get_messages()
                rooms = self.client.get_rooms()
                messages = []
                for r in rooms:
                    if r['room_type'] == 'printer':
                        # print('will get gid:', r['gid'], end='')
                        self.client.enter_room(gid=int(r['gid']))
                        m = self.client.get_messages(gid=int(r['gid']))
                        # print('got message:', m)
                        messages.extend(m)
                # print(messages)
                for m in messages:
                    if m['username'] == self.client.username:
                        continue
                    print(m)
                    try:
                        try:
                            with open('paper.txt', 'r') as f:
                                paper_type = f.read()
                        except FileNotFoundError as e:
                            paper_type = '58'
                            with open('paper.txt', 'w') as f:
                                f.write(paper_type)
                        if '[--image-option--]' in m['text']:
                            option = json.loads(m['text'])['option']
                            self.client.send_message(self.set_option(option), gid=int(m['gid']))
                            continue
                        if '[--font-option--]' in m['text']:
                            option = json.loads(m['text'])['option']
                            family = None
                            size = None
                            if 'font_family' in option:
                                family = option['font_family']
                            if 'font_size' in option:
                                size = int(option['font_size'])
                            self.client.send_message(
                                self.set_font_option(username=m['username'], family=family, size=size),
                                gid=int(m['gid'])
                            )
                            continue
                        if m['type'] == 'image':
                            image = self.client.get_image(m['text'])
                            option = None
                            if m['username'] in self.options:
                                option = self.options[m['username']]
                            # image = image_process(image, option=option)
                            printer = Chat2Printer()
                            printer.print_image(image=image, paper_type=paper_type)
                            self.client.send_message('打印完成！', gid=int(m['gid']))
                        if m['type'] == 'text':
                            text = "@{username}\n{text}".format(username=m['username'], text=m['text'])
                            option = None
                            app.setFont(default_font)
                            if m['username'] in self.font_options:
                                option = self.font_options[m['username']]
                            if option is not None:
                                font = QFont()
                                font.setFamily(option['font-family'])
                                font.setPointSize(option['font-size'])
                                app.setFont(font)
                            printer = Chat2Printer()
                            printer.print_text(text=text, paper_type=paper_type)
                            self.client.send_message('打印完成！', gid=int(m['gid']))
                        time.sleep(1)
                    except Exception as e:
                        print(e)
                        self.client.send_message("打印错误！" + str(e), gid=int(m['gid']))
            except Exception as e:
                print(e)
                self.client.send_message(str(e), gid=1)
            time.sleep(10)

    def quit(self):
        global app
        app.quit()

"""
if __name__ == '__main__':
    font = QFont()
    # font.setFamily("Microsoft YaHei Mono")
    font.setFamily('微软雅黑')
    font.setPointSize(10)
    app = QApplication(sys.argv)
    app.setFont(font)

    # module_test()
    # mini_test()
    friend_test()
    app.quit()
"""

app = QApplication(sys.argv)
default_font = QFont()
default_font.setFamily('微软雅黑')
default_font.setPointSize(10)

if __name__ == '__main__':
    latina = LatinaPrinter()
    if not os.path.exists("save.json"):
        g_username = input("请输入用户名：")
        g_password = input("请输入密码：")
        latina.mainloop(username=g_username, password=g_password)
    latina.mainloop()
