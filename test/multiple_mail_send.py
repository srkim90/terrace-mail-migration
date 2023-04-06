#!env python

import smtplib
import threading
import time
from email.mime.text import MIMEText
from typing import List

MAX_WORK_TH = 32
N_SEND_MAIL = 1200
#MAIL_SERVER = '172.22.1.41'  # '127.0.0.1'
MAIL_SERVER = '127.0.0.1'
MAIL_PORT = 2500

class MultipleMailSend:
    stop_flags: bool
    n_count: int

    def __init__(self) -> None:
        super().__init__()
        self.stop_flags = False
        self.lock = threading.Lock()
        self.n_count = 0
        self.n_work_thread_run = 0

    def __smtp_send_thread_main(self, thread_idx: int):
        self.lock.acquire()
        self.n_work_thread_run += 1
        self.lock.release()
        mail_to = ["srkim@terracetech.co.kr", ]
        str_mail_to = ""
        for uid in mail_to:
            str_mail_to += "%s" % uid

        msg = MIMEText('다우기술 메일보안파트 경력직 채용 과제 테스트 메일 입니다')
        msg['Subject'] = '테스트 메일입니다'
        msg['To'] = str_mail_to[0:-1]

        for idx in range(N_SEND_MAIL):
            if self.stop_flags is True:
                break
            if idx % MAX_WORK_TH != thread_idx:
                continue
            smtp = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
            smtp.ehlo()
            try:
                smtp.sendmail('freeis@terracetech.co.kr', 'srkim@terracetech.co.kr', msg.as_string())
            except smtplib.SMTPDataError:
                pass
            smtp.quit()
            smtp.close()
            self.lock.acquire()
            self.n_count += 1
            self.lock.release()
        #print("mail send thread end : index=%d" % thread_idx)
        self.lock.acquire()
        self.n_work_thread_run -= 1
        self.lock.release()
        return

    def __tps_thread_main(self):
        while self.stop_flags is False:
            time.sleep(1.0)
            self.lock.acquire()
            n_work_thread_run = self.n_work_thread_run
            n_count = self.n_count
            self.lock.release()

            print("send mail : %d/%d, remain work thread=%d" % (n_count, N_SEND_MAIL, n_work_thread_run))

    def __start_tps_threads(self):
        h_thread = threading.Thread(target=self.__tps_thread_main)
        h_thread.daemon = True
        h_thread.start()

    def __start_smtp_threads(self, idx: int):
        h_thread = threading.Thread(target=self.__smtp_send_thread_main, args=(idx,))
        h_thread.daemon = True
        h_thread.start()
        return h_thread

    def run(self):
        h_threads: List[threading.Thread] = []
        self.__start_tps_threads()
        for idx in range(MAX_WORK_TH):
            h_threads.append(self.__start_smtp_threads(idx))
        for h_thread in h_threads:
            h_thread.join()
        time.sleep(1.5)
        return

def main():
    e = MultipleMailSend()
    e.run()


if __name__ == "__main__":
    main()
