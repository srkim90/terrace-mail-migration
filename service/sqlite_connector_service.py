import base64
import os
import sqlite3
from typing import Tuple, List, Union, Dict

from models.day_models import Days
from models.mail_models import MailMessage
from service.logging_service import LoggingService
from service.property_provider_service import ApplicationSettings, application_container
from utils.utills import str_stack_trace, try_bytes_decoding


class SqliteConnector:
    db_path: str
    readonly: bool
    company_id: int
    user_id: int
    is_webfolder: bool
    company_name: str
    setting_provider: ApplicationSettings = application_container.setting_provider
    mail_checker = application_container.mail_file_checker
    logger: LoggingService = application_container.logger
    conn = None
    mbackup_conn = None

    def __init__(self, db_path: str, company_id: int, user_id: int, company_name: str, is_webfolder: bool = False, readonly: bool = True) -> None:
        super().__init__()
        self.readonly = readonly
        self.company_id = company_id
        self.user_id = user_id
        self.company_name = company_name
        self.db_path = db_path
        self.is_webfolder = is_webfolder
        self.conn = self.__db_conn(db_path, readonly)
        self.mbackup_conn = None

    def make_mbackup_conn(self) -> bool:
        db_name: str = self.db_path.replace("_mcache.db", "_mbackup.db")
        if os.path.exists(db_name) is False:
            self.logger.info("[company_id=%s, user_id=%s] not exist _mcache.db : %s, skip, _mbackup.db update" % (self.company_id, self.user_id, db_name,))
            #raise FileNotFoundError("not exist _mcache.db : %s" % (db_name,))
            return False
        self.mbackup_conn = self.__db_conn(db_name, readonly=False)
        return True

    def __db_conn(self, db_path: str, readonly: bool = True):
        if os.path.exists(self.db_path) is False:
            self.logger.minor("Not found sqlite db : path=%s info=(%s)" % (self.db_path, self.__make_log_identify()))
            raise FileNotFoundError("not exist sqlite db : %s" % (self.db_path, ))
        try:
            if readonly is True:
                conn = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True)
            else:
                conn = sqlite3.connect('file:%s' % db_path, uri=True)
        except sqlite3.NotSupportedError as e:
            conn = sqlite3.connect('%s' % db_path)
        #conn.text_factory = str
        conn.text_factory = bytes
        return conn

    def __query_execute(self, cur, query: str) -> None:
        self.logger.debug("sqlite query execute : company_id=%d, user_id=%d, query='%s'" %
                          (self.company_id, self.user_id, query,))
        cur.execute(query)

    def __query_execute_bytes(self, cur, query: str, data: str, coding: str) -> None:
        self.logger.debug("sqlite query execute : company_id=%d, user_id=%d, query='%s', coding=%s" %
                          (self.company_id, self.user_id, query, coding))
        cur.execute(query, (memoryview(data.encode(coding)),))

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

    def commit(self) -> bool:
        if self.conn is not None:
            try:
                self.conn.commit()
            except Exception as e:
                self.logger.error("commit fail : %s\n%s" % (e, str_stack_trace()))
                return False
        else:
            return False
        if self.mbackup_conn is not None:
            self.mbackup_conn.commit()
        return True

    def disconnect(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None
        if self.mbackup_conn is not None:
            self.mbackup_conn.close()
            self.mbackup_conn = None

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

    # def check_mail_exist(self, mail_name: str) -> bool:
    #     exist = False
    #     cur = self.conn.cursor()
    #     self.__query_execute(cur, "select count(*) from mail_message where full_path like('%%" + mail_name + "')")
    #     for row in cur:
    #         count = row[0]
    #         if count > 0:
    #             exist = True
    #         break
    #     cur.close()
    #     return exist

    def get_mail_all_by_hash(self, only_name: bool = False) -> Dict[str, int]:
        mails = self.get_mail_all(only_name)
        result_dict = {}
        for mail in mails:
            result_dict[mail] = 1
        return result_dict


    def get_mail_all(self, only_name: bool = False) -> List[str]:
        mail_list: List[str] = []
        cur = self.conn.cursor()
        self.__query_execute(cur, "select full_path from mail_message")
        for row in cur:
            is_charset_ok, full_path, coding = try_bytes_decoding(row[0])
            if is_charset_ok is False:
                continue
            if only_name is True:
                full_path = full_path.replace("\\", "/").split("/")[-1]
            mail_list.append(full_path)
        cur.close()
        return mail_list


    def get_target_mail_count(self, days: Union[Days, None]) -> Tuple[int, int]:
        size = 0
        count = 0
        cur = self.conn.cursor()
        self.__query_execute(cur, "select count(*), sum(msg_size) from mail_message" + self.__make_where(days))
        for row in cur:
            count = row[0]
            size = row[1]
            break
        cur.close()
        if size is None and count == 0:
            size = 0
        return count, size

    # def mail_message_exist(self, folder_no: int, uid_no: int) -> bool:
    #     return False if self.__get_mail_file_name_in_db(folder_no, uid_no) is None else True

    def get_mail_file_name_in_db(self, folder_no: int, uid_no: int) -> Union[str, None]:
        full_path = None
        cur = self.conn.cursor()
        self.__query_execute(cur,
            "select full_path from mail_message where folder_no = %d and uid_no = %d" % (folder_no, uid_no))
        for idx, row in enumerate(cur):
            is_charset_ok, full_path, coding = try_bytes_decoding(row[0])
            if is_charset_ok is False:
                continue
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
        if "\\" in eml_file_name: ## 윈도우 테스트 환경 일 경우 (윈도우 불편.. ㅠㅠ, 맥을 사달라!)
            eml_file_name = eml_file_name.split("\\")[-1]

        if eml_file_name not in old_full_path:
            self.logger.error("Error.  : %s" % self.__make_log_identify(folder_no=folder_no,
                                                                                       uid_no=uid_no,
                                                                                       message=new_full_path, ))
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

    def __check_windows_dir(self, path: str):
        if "\\" not in path:
            return path
        test_path = self.setting_provider.report.local_test_data_path
        if test_path is not None:
            return path.replace(test_path, "").replace("\\", "/")
        return path

    def update_mbackup(self, folder_no: int, uid_no: int, new_full_path: str, coding: str):
        if self.mbackup_conn is None:
            return
        cur = self.mbackup_conn.cursor()
        #new_full_path = self.__check_windows_dir(new_full_path)
        #sql = "update mail_message set full_path = '%s' where folder_no = %d and uid_no = %d" % (
        #   new_full_path, folder_no, uid_no)
        new_full_path = self.__check_windows_dir(new_full_path)
        sql = "update mail_message set full_path = ? where folder_no = %d and uid_no = %d" % (
             folder_no, uid_no)
        self.__query_execute_bytes(cur, sql, new_full_path, coding)
        cur.close()
        return


    def update_mail_path(self, folder_no: int, uid_no: int, new_full_path: str, old_full_path: str, coding: str, check_validate: bool = True) -> bool:
        if check_validate is True:
            if self.__validate_eml_path(new_full_path, old_full_path, folder_no, uid_no) is False:
                return False
        cur = self.conn.cursor()
        # sql = "update mail_message set full_path = '%s' where folder_no = %d and uid_no = %d" % (
        #     self.__check_windows_dir(new_full_path), folder_no, uid_no)
        new_full_path = self.__check_windows_dir(new_full_path)
        sql = "update mail_message set full_path = ? where folder_no = %d and uid_no = %d" % (
             folder_no, uid_no)
        self.__query_execute_bytes(cur, sql, new_full_path, coding)
        cur.close()
        return True

    def get_target_mail_list(self, days: Days) -> List[MailMessage]:
        cur = self.conn.cursor()
        messages: List[MailMessage] = []
        self.__query_execute(cur,
            "select folder_no, uid_no, full_path, msg_size, msg_receive from mail_message" + self.__make_where(days))

        try:
            messages = []
            for row in cur:
                b64_bytes_full_path: str = "utf-8"
                bytes_full_path:bytes = row[2]
                is_charset_ok, full_path, coding = try_bytes_decoding(bytes_full_path)
                folder_no:int = row[0]
                uid_no:int = row[1]
                if is_charset_ok is False or coding != "utf-8": # 파일 이름 인코딩이 UTF-8 이 아닐 경우, 디버깅을 위해 b64로 값을 찍어둔다.
                    b64_bytes_full_path = base64.b64encode(bytes_full_path).decode("utf-8")
                if is_charset_ok is False:
                    self.logger.info("Fail to decode full_path=%s, bytes_full_path=%s, db_path=%s, company_name=%s, company_id=%d, user_id=%d, folder_no=%d, uid_no=%d"
                                 % (b64_bytes_full_path, bytes_full_path, self.db_path, self.company_name, self.company_id, self.user_id, folder_no, uid_no))
                    continue
                messages.append(MailMessage(
                    folder_no=folder_no,
                    uid_no=uid_no,
                    full_path=full_path,
                    email_file_coding=coding,
                    bytes_full_path=b64_bytes_full_path,
                    msg_size=row[3],
                    msg_receive=row[4],
                    st_ctime=0.0,
                    st_ino=0,
                    st_size=0,
                    hardlink_count=0,
                    is_webfolder=self.is_webfolder,
                    hardlinks=[]
                ))
        except sqlite3.OperationalError as e:
            self.logger.error("[get_target_mail_list] Error %s : \n%s" % (e, str_stack_trace()))
            pass
        cur.close()
        return messages
