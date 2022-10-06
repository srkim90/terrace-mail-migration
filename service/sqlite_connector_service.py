import logging
import os
import sqlite3
from typing import Tuple, List, Union

from models.day_models import Days
from models.mail_models import MailMessage
from service.logging_service import LoggingService
from service.property_provider_service import ApplicationSettings, ApplicationContainer


class SqliteConnector:
    db_path: str
    readonly: bool
    company_id: int
    user_id: int
    company_name: str
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()
    mail_checker = ApplicationContainer().mail_file_checker()
    logger: LoggingService = ApplicationContainer().logger()

    def __init__(self, db_path: str, company_id: int, user_id: int, company_name: str, readonly: bool = True) -> None:
        super().__init__()
        self.conn = None
        self.readonly = readonly
        self.company_id = company_id
        self.user_id = user_id
        self.company_name = company_name
        self.db_path = db_path
        if os.path.exists(self.db_path) is False:
            self.logger.minor("Not found sqlite db : path=%s info=(%s)" % (self.db_path, self.__make_log_identify()))
            raise FileNotFoundError
        try:
            if readonly is True:
                self.conn = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True)
            else:
                self.conn = sqlite3.connect('file:%s' % db_path, uri=True)
        except sqlite3.NotSupportedError as e:
            self.conn = sqlite3.connect('%s' % db_path)

    def __check_eml_data(self, full_path: str) -> (float, int, int):
        stat: os.stat_result = self.mail_checker.check_file_status(full_path)
        return stat.st_ctime, stat.st_ino, stat.st_size

    def __make_log_identify(self, folder_no: int = -1, uid_no: int = -1, message: str = ""):
        log_identify = "company_id=%d(%s), user_id=%d, readonly=%s" % (
        self.company_id, self.company_name, self.user_id, self.readonly)
        if folder_no != -1:
            log_identify += " folder_no=%d" % folder_no
        if uid_no != -1:
            log_identify += " uid_no=%d" % uid_no
        if len(message) > 0:
            log_identify += " : %s" % message
        return log_identify

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __make_where(self, days: Union[Days, None]):
        if days is None:
            return ""
        s_timestamp = days.get_start_day_timestamp()
        e_timestamp = days.get_end_day_timestamp()
        if e_timestamp is None:
            return ""
        sub_query = " where msg_receive < %s" % e_timestamp
        if s_timestamp is not None:
            sub_query += " and msg_receive > %s" % s_timestamp
        return sub_query

    def get_target_mail_count(self, days: Union[Days, None]) -> Tuple[int, int]:
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

    def __get_mail_file_name_in_db(self, folder_no: int, uid_no: int) -> Union[str, None]:
        full_path = None
        cur = self.conn.cursor()
        cur.execute(
            "select full_path from mail_message where folder_no = %d and uid_no = %d" % (folder_no, uid_no))
        for idx, row in enumerate(cur):
            full_path = row[0]
            if idx != 0:
                self.logger.error("__get_mail_file_name_in_db not unique: %s" % self.__make_log_identify(folder_no=folder_no,
                                                                                                 uid_no=uid_no))
        return full_path

    def __validate_eml_path(self, new_full_path, old_full_path, folder_no: int, uid_no: int):
        if new_full_path == old_full_path:
            self.logger.error(
                "Error. old file and new file is same : %s" % self.__make_log_identify(folder_no=folder_no,
                                                                                       uid_no=uid_no,
                                                                                       message=new_full_path, ))
            return False
        if os.path.exists(new_full_path) is False:
            self.logger.error("Error. Not found new mail path : %s" % self.__make_log_identify(folder_no=folder_no,
                                                                                       uid_no=uid_no,
                                                                                       message=new_full_path, ))
            return False
        eml_file_name = new_full_path.split("/")[-1]
        if eml_file_name not in old_full_path:
            return False
        old_ctime, old_ino, old_size = self.__check_eml_data(new_full_path)
        new_ctime, new_ino, new_size = self.__check_eml_data(old_full_path)
        if old_size != new_size or old_size == 0:
            self.logger.error("Error. not compare mail size old and now : %s" % self.__make_log_identify(folder_no=folder_no,
                                                                                                 uid_no=uid_no,
                                                                                                 message=new_full_path,
                                                                                                 ))
            return False
        return True

    def update_mail_path(self, folder_no: int, uid_no: int, new_full_path: str) -> bool:
        old_full_path = self.__get_mail_file_name_in_db(folder_no, uid_no)
        if self.__validate_eml_path(new_full_path, old_full_path, folder_no, uid_no) is False:
            return False
        cur = self.conn.cursor()
        cur.execute("update mail_message set full_path = %s from mail_message where folder_no = %d uid_no = %d" % (
            new_full_path, folder_no, uid_no))
        return True

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
