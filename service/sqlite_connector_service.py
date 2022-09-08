import logging
import sqlite3
from typing import Tuple, List

from models.day_models import Days
from models.mail_models import MailMessage
from service.property_provider_service import ApplicationSettings, ApplicationContainer

log = logging.getLogger(__name__)


class SqliteConnector:
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()

    def __init__(self, db_path: str) -> None:
        self.conn = None
        super().__init__()
        self.conn = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True)

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __make_where(self, days: Days):
        s_timestamp = days.get_start_day_timestamp()
        e_timestamp = days.get_end_day_timestamp()
        if e_timestamp is None:
            return ""
        sub_query = " where msg_receive < % s" % e_timestamp
        if s_timestamp is not None:
            sub_query += " and msg_receive > %s" % s_timestamp
        return sub_query

    def get_target_mail_count(self, days: Days) -> Tuple[int, int]:
        size = 0
        count = 0
        cur = self.conn.cursor()
        cur.execute("select count(*), sum(msg_size) from mail_message" + self.__make_where(days))
        for row in cur:
            count = row[0]
            size = row[1]
            break
        cur.close()
        if size is None and count == 0:
            size = 0
        return count, size

    def get_target_mail_list(self, days: Days) -> List[MailMessage]:
        cur = self.conn.cursor()
        messages: List[MailMessage] = []
        cur.execute(
            "select folder_no, uid_no, full_path, msg_size, msg_receive from mail_message" + self.__make_where(days))
        for row in cur:
            messages.append(MailMessage(
                folder_no=row[0],
                uid_no=row[1],
                full_path=row[2],
                msg_size=row[3],
                msg_receive=row[4],
                st_ctime=0.0,
                st_ino=0,
                st_size=0,
                hardlink_count=0,
                hardlinks=[]
            ))
        cur.close()
        return messages
