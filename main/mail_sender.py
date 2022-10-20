from common_import import *
from main.cmd.command_line_parser import read_sender_options
from main.cmd.mail_sender_option_models import SenderCommandOptions
from service.mail_send_service import send_all

if __name__ == "__main__":
    option: SenderCommandOptions = read_sender_options()
    send_all(option.mail_to, option.n_send_mail)