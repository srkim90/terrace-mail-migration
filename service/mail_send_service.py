import gzip
import os
import platform
import random
import smtplib
from typing import Union, List


class MailSendService:
    def __init__(self, server_host: str, port: int, sender_uid: str, sender_pw: str) -> None:
        super().__init__()
        self.server_host = server_host
        self.port = port
        self.sender_uid = sender_uid
        self.sender_pw = sender_pw
        if "window" in platform.system().lower():
            self.base_path = "D:\\data\\terracehamadm"
        else:
            self.base_path = "/opt/mail-migration-data/terracehamadm"

    @staticmethod
    def read_qs(mail_path: str) -> bytes:
        mail_data: bytes
        if mail_path.split(".")[-1].lower() == "gz":
            fd = gzip.open(mail_path, "rb")
        else:
            fd = open(mail_path, "rb")
        mail_data = fd.read()
        new_data: bytes = b''
        for idx, line in enumerate(mail_data.split(b'\n')):
            if idx == 0:
                continue
            if b'^^^^^^^^+_~!spacelee@$%^&!@#)_,$^^^^^^^^^^' in line:
                break
            new_data += line + b'\n'
        fd.close()
        return new_data

    def send_mail(self, receiver_addrs: Union[str, List[str]], mail_paths: Union[str, List[str]]):
        if type(mail_paths) == str:
            mail_paths = [mail_paths, ]
        if len(mail_paths) == 0:
            print("Not exist mail to send : base_path=%s" % (self.base_path,))
            return
        if type(receiver_addrs) == str:
            receiver_addrs = [receiver_addrs,]
        smtp = None
        for idx, mail_path in enumerate(mail_paths):
            if smtp is None:
                smtp = smtplib.SMTP(self.server_host, self.port)
                smtp.login(self.sender_uid, self.sender_pw)
            message = self.read_qs(mail_path)
            rr_idx = idx % len(receiver_addrs)
            smtp.sendmail(from_addr=self.sender_uid, to_addrs=receiver_addrs[rr_idx], msg=message)
            print("send mail : [%d/%d] %s" % (idx, len(mail_paths), mail_path))
            if idx % 10 == 0 and idx != 0:
                smtp.close()
                smtp = None

    def load_mail_data(self, load_count: int = -1) -> List[str]:
        result = []
        mail_fills = []
        if os.path.exists(self.base_path) is False:
            return []
        for (root, dirs, files) in os.walk(self.base_path):
            for item in files:
                if ".qs" not in item:
                    continue
                mail_fills.append(os.path.join(root, item))
        random.shuffle(mail_fills)
        for idx, mail_item in enumerate(mail_fills):
            if load_count != -1 and load_count <= idx:
                break
            result.append(os.path.join(self.base_path, mail_item))
        return result


def send_all(mail_to: Union[str, List[str]], n_send_mail: int = -1):
    e = MailSendService("127.0.0.1", 25, "srkim@abctest.co.co", "port2093@")
    mail_list = e.load_mail_data(n_send_mail)
    e.send_mail(mail_to, mail_list)
    return


if __name__ == "__main__":
    mail_to = "srkim@abctest.co.co"
    n_send_mail = 10
    send_all(mail_to, n_send_mail)
