#!/bin/env python3

import sys
import redis
import smtplib
import os
import uuid
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from toml import loads
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from email.utils import  parseaddr


class Users(object):
    def __init__(self, host, port, password=None):
        self.con = redis.StrictRedis(host=host, port=port, password=password)
    def get(self, id):
        return self.con.get(id)
    def remove(self, id):
        try:
            self.con.delete('id')
        except:
            return False
        finally:
            return True
    def set(self, id, email):
        try:
            self.con.set(id, email)
        except:
            return False
        finally:
            return True
    def exists(self, id):
        return self.con.exists(id)


class Mail(object):
    def __init__(self, user, password, smtp_server_ip, smtp_server_port, smtp_server_ssl = False):
        self._user = user
        self._password = password
        self._smtp_server_ip = smtp_server_ip
        self._smtp_server_port = smtp_server_port
        self._smtp_server_ssl = smtp_server_ssl
    def send(self, target_email, file_path, file_name):
        ret = True
        print(file_path)
        try:
            msg = MIMEMultipart()

            msg['From'] = formataddr(["KindleBot", self._user])
            msg['To'] = formataddr(["kindle", target_email])
            msg['Subject'] = file_name
            print(file_name)


            # 构造附件1，传送当前目录下的 test.txt 文件
            att1 = MIMEText(open(file_path, 'rb').read(), 'base64', 'utf-8')
            att1["Content-Type"] = 'application/octet-stream'
            # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
            # att1["Content-Disposition"] = 'attachment; filename=%s' % file_name
            att1.add_header("Content-Disposition", 'attachment', filename=file_name)
            msg.attach(att1)

            if self._smtp_server_ssl:
                server = smtplib.SMTP_SSL(self._smtp_server_ip, self._smtp_server_port)
            else:
                server = smtplib.SMTP(self._smtp_server_ip, self._smtp_server_port)
            server.login(self._user, self._password)  # 括号中对应的是发件人邮箱账号、邮箱密码
            # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.sendmail(self._user, [target_email, ], msg.as_string())
            server.quit()  # 关闭连接
        except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
            ret = False
        if ret:
            print("Success")
        else:
            print("Fail")
        return ret

class Bot(object):
    def __init__(self, configs):
        self.updater = Updater(configs['bot']['token'], request_kwargs=configs['bot']['proxy_args'])
        self.dispatcher = self.updater.dispatcher

        self.mail = Mail(
            configs["email"]["user"],
            configs["email"]["password"],
            configs["email"]["server"]["ip"],
            configs["email"]["server"]["port"],
            configs["email"]["server"]["ssl"]
            )
        
        database_password = None if "password" not in  configs["database"].keys() else configs["database"]["password"]
        self.users = Users(configs["database"]["host"], configs["database"]["port"])

        self.temp_path = 'TEMP/'
        if not os.path.exists(self.temp_path):
            os.mkdir(self.temp_path)

        self.dispatcher.add_handler(self.text_handler())
        self.dispatcher.add_handler(self.help_handler())
        self.dispatcher.add_handler(self.file_handler())
        self.dispatcher.add_handler(self.email_handler())
        self.dispatcher.add_handler(self.get_mail_handler())
        self.dispatcher.add_handler(CommandHandler('start', self.help))


    def start(self):
        self.updater.start_polling()

    def stop(self):
        self.updater.stop()

    def help(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, parse_mode="MARKDOWN", text="""
您好，欢迎您使用 xHama 组织开发的 KindleBot！
请您先绑定您的 kindle 地址，请注意在绑定您的 kindle 地址的同时，
请把我们的邮箱 kindle@dengqi.org 添加到您的 kindle 白名单里:

[参考](https://www.amazon.cn/gp/help/customer/display.html?nodeId=201974240)

```
绑定方法:
/email [kindle 邮箱]
    - kindle 邮箱是由亚马逊分配的设备唯一的邮箱，一般格式：xxx_xx@kindle.cn

```            

使用方法:

直接把 document 发送给 bot 即可。 其中 `mobi`, `txt`, `pdf`, `html` 文件将会直接发送到您的设备。
`epub` 文件将会经由服务器处理以后发送到您的设备。

**我们承诺，在您的文档成功的发送到您的设备之后，我们会将文档完整的从我们的服务器上删除。**
                """)

    def help_handler(self):
        return CommandHandler('help', self.help)

    def email_handler(self):
        def set_email(bot, update):
            user_id = update.message.from_user.id
            chat_id = update.message.chat_id
            email = update.message.text
            email = email.replace(' ','')
            email = email.replace('\t','')
            email = email.replace('/email','')
            print(email)
            print(len(email))
            print(user_id)
            parase_data = parseaddr(email)
            if parase_data == ('', ''):
                bot.send_message(chat_id, text="你输入的邮箱地址不正确！")
            else:
                self.users.remove(str(user_id))
                res = self.users.set(str(user_id), email)
                if res:
                    bot.send_message(chat_id, text="邮箱绑定成功！")
                else:
                    bot.send_message(chat_id, text="邮箱绑定失败！")
        return CommandHandler('email', set_email)

    def get_mail_handler(self):
        def get_email(bot, update):
            user_id = update.message.from_user.id
            chat_id = update.message.chat_id
            if self.users.exists(user_id):
                user_email = str(self.users.get(user_id))
                bot.send_message(chat_id, text="您的邮箱是 %s" % user_email)
            else:
                bot.send_message(chat_id, text="您还没有绑定邮箱！")
        return CommandHandler('get', get_email)

    @staticmethod
    def text_handler():
        def text_replay(bot, update):
            bot.send_message(chat_id=update.message.chat_id, text="伦家只是 **kindle 机器人**，不接受调戏哦！", parse_mode="MARKDOWN")

        return MessageHandler(Filters.text, text_replay)

    def file_handler(self):
        def file_replay(bot, update):
            # Information about message
            recv_document = update.message.document
            user_id = update.message.from_user.id
            chat_id = update.message.chat_id
            #information about document
            file_name = recv_document.file_name
            file_size = recv_document.file_size
            file_extension = os.path.splitext(file_name)[1][1:]
            print(file_extension)
            print("File name: %s, File size: %s" %(file_name, file_size))
            #if user is not set email
            print(user_id)
            if not self.users.exists(user_id):
                bot.send_message(chat_id, text="您还没有绑定邮箱，请您先绑定邮箱！")
                return
            user_email = str(self.users.get(user_id))[2:-1]
            print(user_email)

            if file_extension in ['html', 'mobi', 'txt']:
                temp_file_path = os.path.join(self.temp_path, str(uuid.uuid4()) +"."+file_extension)
                recv_document.get_file().download(temp_file_path)
                bot.send_message(chat_id, text="文件收到，正在飞快的传输到您的 Kindle 之中！")
                ret = self.mail.send(user_email, temp_file_path, file_name)
                if ret:
                    bot.send_message(chat_id, text="文件发送成功，稍等片刻即可开始阅读啦！")
                    try:
                        os.remove(temp_file_path)
                    except OSError:
                        pass
                else:
                    bot.send_message(chat_id, text="由于未知原因，文件发送失败，请稍后重试！")

            elif file_extension in ['epub']:
                bot.send_message(chat_id, text="文件格式需要转换")
            else:
                bot.send_message(chat_id=chat_id, text="对不起，文件格式暂不支持！")

        return MessageHandler(Filters.document, file_replay)



def help():
    print("""
Kindle Bot Usage:

python3 app.py -c config.toml

""")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        help()
    elif sys.argv[1] != "-c":
        help()
    else:
        configs = loads(open(sys.argv[2], 'r').read())
        bot = Bot(configs)
        bot.start()