import os
import shutil

from models.mail_models import MailMessage
from service.sqlite_connector_service import SqliteConnector


def test_move(mail: MailMessage):
    org_full_path = mail.bytes_full_path
    with open(org_full_path, "w") as fd:
        fd.write("1111")

    #shutil.copy2(org_full_path, mail.full_path)



def main() -> None:
    conn = SqliteConnector("C:\\Users\\DAOU\Desktop\\261_34_6160\\_mcache.db",
                           1, 1, "test_company", False)
    mail_list = conn.get_target_mail_list(None)
    mail_0: MailMessage = mail_list[0]
    mail_1: MailMessage = mail_list[1]
    mail_2: MailMessage = mail_list[2]
    mail_3: MailMessage = mail_list[3]
    os.chdir('C:\\Users\\DAOU\\Desktop\\261_34_6160')
    test_move(mail_0)
    test_move(mail_1)
    test_move(mail_2)
    test_move(mail_3)



    return

if __name__ == '__main__':
    main()
