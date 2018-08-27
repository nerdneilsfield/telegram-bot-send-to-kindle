#!/usr/bin/python3

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr


my_user = 'dengqi935@outlook.com'      # 收件人邮箱账号，我这边发送给自己

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
