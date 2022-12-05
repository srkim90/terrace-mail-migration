from models.mail_models import MailMessage
from service.sqlite_connector_service import SqliteConnector


def update_fn(mail, new_full_path, codding, conn):
    mail.email_file_coding = codding
    if conn.update_mail_path(mail.folder_no, mail.uid_no, new_full_path, mail.full_path, mail.email_file_coding,
                             check_validate=False) is True:
        conn.commit()


def main() -> None:
    conn = SqliteConnector("C:\\Users\\DAOU\Desktop\\261_34_6160\\_mcache.db",
                           1, 1, "test_company", False)
    mail_list = conn.get_target_mail_list(None)
    mail_0: MailMessage = mail_list[0]
    mail_1: MailMessage = mail_list[1]
    mail_2: MailMessage = mail_list[2]
    mail_3: MailMessage = mail_list[3]

    mail = mail_0
    coding = "utf-8"
    new_full_path = "1. 테스트테스트_" + coding
    update_fn(mail, new_full_path, coding, conn)

    mail = mail_1
    coding = "euc-kr"
    new_full_path = "2. 테스트테스트_" + coding
    update_fn(mail, new_full_path, coding, conn)

    mail = mail_2
    coding = "euc-jp"
    new_full_path = "3. ホイールセットも出荷に同じように2週間かかりますか？" + coding
    update_fn(mail, new_full_path, coding, conn)

    mail = mail_3
    coding = "cp949"
    new_full_path = "4. 테스트테스트_" + coding
    update_fn(mail, new_full_path, coding, conn)

    return


if __name__ == '__main__':
    main()
