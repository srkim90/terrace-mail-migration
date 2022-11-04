from common_import import *
from main.cmd.command_line_parser import read_sender_options
from main.cmd.mail_sender_option_models import SenderCommandOptions
from service.mail_send_service import send_all

if __name__ == "__main__":
    option: SenderCommandOptions = read_sender_options()
    mail_to = []
    for idx in range(100, 333):
        if idx == 111 or idx == 123:
            continue
        mail_to.append("srkim%d@srkim.kr" % idx)
    option.mail_to = mail_to
    send_all(option.mail_to, option.to_all, n_send_mail=option.n_send_mail)