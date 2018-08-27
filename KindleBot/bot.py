from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import toml
import os
import uuid
import re
from email.utils import  parseaddr

from KindleBot.mail import  Mail
from KindleBot.database import Users

TOKEN = ""
REQUEST_KWARGS = ""

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


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


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], 'r') as config:
        configs = toml.loads(config.read())
        TOKEN = configs["token"]
        REQUEST_KWARGS = configs["request_kwargs"]

    bot = KindleBot(TOKEN, REQUEST_KWARGS)
    bot.start()
