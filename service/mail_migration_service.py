import logging
import os
import platform
import random
import shutil
from typing import Union, Tuple, List

from enums.move_strategy_type import MoveStrategyType
from models.company_models import Company
from models.mail_models import MailMessage
from models.user_models import User
from service.logging_service import LoggingService
from service.mail_migration_logging_service import MailMigrationLoggingService
from service.property_provider_service import ApplicationSettings, application_container
from service.sqlite_connector_service import SqliteConnector
from utils.utills import handle_userdata_if_windows, is_windows


class MailMigrationService:
    company: Company
    report_file_name: str
    is_window: Union[bool, None]
    logger: LoggingService = application_container.logger
    migration_logging: MailMigrationLoggingService = application_container.migration_logging
    setting_provider: ApplicationSettings = application_container.setting_provider

    def __init__(self, company: Company) -> None:
        super().__init__()
        self.company = company
        self.is_window = None
        self.dir_separator = "\\" if self.__is_windows() else "/"
        self.move_setting = self.setting_provider.move_setting
        self.migration_logging.start_stat()

    def __is_windows(self) -> bool:
        if self.is_window is not None:
            return self.is_window
        self.is_window = "window" in platform.system().lower()
        return self.is_window

    def __check_origin_mdata_path(self, org_full_path: str) -> bool:
        for valid_path in self.move_setting.origin_mdata_path:
            if valid_path in org_full_path:
                return True
        return False

    def __calc_volume_used_ratio(self, path: str):
        if is_windows() is True:
            return 0.0
        info = os.statvfs(path)
        size = info.f_bsize * info.f_blocks
        free = info.f_bsize * info.f_bavail
        return (1.0 - (free / size)) * 100.0

    def __select_move_target_dir(self) -> str:
        threshold_ratio = self.move_setting.partition_capacity_threshold_ratio
        strategy: MoveStrategyType = self.move_setting.move_strategy
        avail_list = []
        for path in self.move_setting.new_mdata_path:
            ratio = self.__calc_volume_used_ratio(path)
            if ratio >= threshold_ratio:
                continue
            avail_list.append([ratio, path, ])
        if strategy == MoveStrategyType.RANDOM or strategy == MoveStrategyType.ROUND_ROBIN:
            return avail_list[random.randrange(0, len(avail_list))][1]
        elif strategy == MoveStrategyType.REMAINING_CAPACITY_HIGHER_PRIORITY:
            return max(avail_list)[0]
        elif strategy == MoveStrategyType.REMAINING_CAPACITY_LOWER_PRIORITY:
            return min(avail_list)[0]

    def __m_data_subdir_parser(self, org_full_path: str):
        org_path_slice = org_full_path.split(self.dir_separator)
        if len(org_path_slice) < 6:
            self.logger.info("Invalid path of email : %s" % (org_full_path,))
            return None
        eml_name = org_path_slice[-1]
        yyyymmdd = org_path_slice[-2]
        index3 = org_path_slice[-3]
        index2 = org_path_slice[-4]
        index1 = org_path_slice[-5]
        if eml_name.split(".")[-1] != "eml":
            self.logger.info("Invalid path of email : %s" % (org_full_path,))
            return None
        return os.path.join(index1, index2, index3, yyyymmdd)

    def __copy_mail_file(self, org_full_path: str) -> Union[str, None]:
        new_mdata_path = self.__select_move_target_dir()
        if self.__check_origin_mdata_path(org_full_path) is False:
            self.logger.debug("application.yml 파일에 지정 된 원본 파일 위치와 입력된 파일의 위치가 다릅니다. (SKIP) : org_full_path=%s, %s" %
                              (org_full_path, self.__make_log_identify()))
            return None
        elif new_mdata_path is None:
            self.logger.error("이동 대상 디렉토리가 존재하지 않거나, 유효하지 않습니다. : new_mdata_path=%s, %s" %
                              (self.move_setting.new_mdata_path, self.__make_log_identify()))
            return None
        file_name = org_full_path.split(self.dir_separator)[-1]
        new_dir = os.path.join(self.__select_move_target_dir(), self.__m_data_subdir_parser(org_full_path))
        new_dir = os.path.join(new_mdata_path, new_dir)
        if os.path.exists(new_dir) is False:
            os.makedirs(new_dir)
        full_new_file = os.path.join(new_dir, file_name)
        if os.path.exists(full_new_file) is True:
            self.logger.minor("메일 이동 대상 경로에 이미 다른 파일이 존재합니다. : full_new_file=%s, %s" %
                              (full_new_file, self.__make_log_identify()))
            return None
        shutil.copy2(org_full_path, full_new_file)
        self.migration_logging.inc_mail_copy()
        self.migration_logging.inc_disk_write(os.stat(full_new_file).st_size)
        return full_new_file

    def __make_log_identify(self, user: User = None, message: str = ""):
        log_identify = "company_id=%d(%s)" % (self.company.id, self.company.name)
        if user is not None:
            log_identify += ", user_id=%d" % (user.id,)
        if len(message) > 0:
            log_identify += " : %s" % message
        return log_identify

    def __move_a_file(self, user: User, mail: MailMessage, sqlite: SqliteConnector) -> Tuple[bool, Union[str, None]]:
        old_full_path = sqlite.get_mail_file_name_in_db(mail.folder_no, mail.uid_no)
        if old_full_path is None:
            self.migration_logging.inc_migration_fail_already_removed()
            return False, None
        org_full_path = mail.full_path
        new_full_path = self.__copy_mail_file(org_full_path)
        if new_full_path is None:
            self.migration_logging.inc_migration_fail_invalid_new_directory()
            self.logger.minor("Fail to create new mail file: %s" % self.__make_log_identify(user))
            return False, None
        self.migration_logging.inc_sqlite_update_query()
        result = sqlite.update_mail_path(mail.folder_no, mail.uid_no, new_full_path, old_full_path)
        if result is False:
            os.remove(new_full_path)
            self.migration_logging.inc_migration_fail_sqlite_db_update_fail()
            self.migration_logging.inc_mail_delete_as_fail()
            return False, None
        else:
            #os.remove(org_full_path)
            sqlite.update_mbackup(mail.folder_no, mail.uid_no, new_full_path)
            self.migration_logging.inc_mail_delete()
            return True, org_full_path

    def __handle_a_user(self, user: User) -> bool:
        company = self.company
        old_mails_to_delete: List[str] = []
        user = handle_userdata_if_windows(user, self.setting_provider.report.local_test_data_path)
        self.logger.minor("start user mail transfer: %s" % self.__make_log_identify(user))
        try:
            sqlite_db_file_name = os.path.join(user.message_store, "_mcache.db")
            conn = SqliteConnector(sqlite_db_file_name, company.id, user.id, company.name,
                                     readonly=False)
            conn.make_mbackup_conn()
            self.migration_logging.inc_sqlite_db_open()
        except Exception as e:
            self.logger.error("start user mail transfer error: %s, error-message=%s"
                              % (self.__make_log_identify(user), e))
            return False

        for idx, mail in enumerate(user.messages):
            is_success = False
            delete_mail_path = None
            self.migration_logging.inc_migration_try()

            try:
                is_success, delete_mail_path = self.__move_a_file(user, mail, conn)
            except Exception as e:
                self.logger.error(
                    "Error. fail in __move_a_file : uid=%d, company_id=%d, mail_uid_no=%d, folder_no=%d, e=%s"
                    % (user.id, company.id, mail.uid_no, mail.folder_no, e))
                self.migration_logging.inc_migration_fail_unexpected_error()
            if is_success is True:
                self.migration_logging.inc_migration_success()
                old_mails_to_delete.append(delete_mail_path)
            else:
                self.migration_logging.inc_migration_fail()
        if conn.commit() is True:
            for old_mail in old_mails_to_delete:
                os.remove(old_mail)
        conn.disconnect()
        self.migration_logging.inc_sqlite_db_close()
        return True

    def run(self, user_id: int = None):
        self.logger.info("=====================================================")
        self.logger.info("start company mail transfer: %s" % self.__make_log_identify())
        for idx, user in enumerate(self.company.users):
            if user_id is not None and user.id != user_id:
                continue
            self.__handle_a_user(user)
        self.logger.info("=====================================================")
        self.logger.info("end company mail transfer: %s" % self.__make_log_identify())
        self.logger.info("=====================================================")
