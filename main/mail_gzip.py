from common_import import *
from service.mail_gzip_service import MailGzipService


def main():
    base_dir = "D:\\data\\report\\20221115_162924\\10"
    e = MailGzipService(base_dir)
    e.run()


if __name__ == "__main__":
    main()
