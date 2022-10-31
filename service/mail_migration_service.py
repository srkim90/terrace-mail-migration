import datetime
import logging
import os
import platform
import random
import shutil
from typing import Union, Tuple, List, Dict

from enums.migration_result_type import UserMigrationResultType, MailMigrationResultType
from enums.move_strategy_type import MoveStrategyType
from models.company_migration_result_models import CompanyMigrationResult, save_company_migration_report_as_json
from models.company_models import Company
from models.mail_migration_result_models import MailMigrationResult
from models.mail_models import MailMessage
from models.user_migration_result_models import UserMigrationResult
from models.user_models import User
from service.logging_service import LoggingService
from service.mail_migration_logging_service import MailMigrationLoggingService
from service.property_provider_service import ApplicationSettings, application_container
from service.signal_service import get_stop_flags
from service.sqlite_connector_service import SqliteConnector
from utils.utills import handle_userdata_if_windows, is_windows, str_stack_trace


class MailMigrationService:
    inode_checker: Dict[int, str]
    company: Company
    report_file_name: str
    is_window: Union[bool, None]
    logger: LoggingService = application_container.logger
    migration_logging: MailMigrationLoggingService = application_container.migration_logging
    setting_provider: ApplicationSettings = application_container.setting_provider
    company_stat: CompanyMigrationResult

    def __init__(self, company: Company) -> None:
        super().__init__()
        self.company = company
        self.is_window = None
        self.dir_separator = "\\" if self.__is_windows() else "/"
        self.move_setting = self.setting_provider.move_setting
        self.migration_logging.start_stat()
        self.company_stat = self.__init_statistic()
        self.inode_checker = {}

    def __init_statistic(self) -> CompanyMigrationResult:
        return CompanyMigrationResult(
            id=self.company.id,
            counting_date_range=self.company.counting_date_range,
            start_at=datetime.datetime.now(),
            end_at=None,
            time_consuming=None,
            domain_name=self.company.domain_name,
            name=self.company.name,
            site_url=self.company.site_url,
            n_migration_user_target=len(self.company.users),
            n_migration_user_success=0,
            n_migration_user_fail=0,
            n_migration_mail_target=self.company.user_all_mail_count,
            n_migration_mail_success=0,
            n_migration_mail_fail=0,
            user_result_type_classify={},
            mail_result_type_classify={},
            company_mail_size=self.company.company_mail_size,
            results=[]
        )

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

    @staticmethod
    def __check_eml_ext(eml_name: str) -> bool:
        check_list_1 = ["eml", "qs", "qm"]
        check_list_2 = ["eml.gz", "qs.gz", "qm.gz"]
        eml_slice = eml_name.split(".")
        ext_1 = eml_slice[-1].lower()
        ext_2 = None
        if len(eml_slice) >= 3:
            ext_2 = "%s.%s" % (eml_name.split(".")[-2].lower(), ext_1)
        if ext_1 in check_list_1:
            return True
        if ext_2 is not None and ext_2 in check_list_2:
            return True
        return False

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
        if self.__check_eml_ext(eml_name) is False:
            self.logger.info("Invalid path of email : %s" % (org_full_path,))
            return None
        return os.path.join(index1, index2, index3, yyyymmdd)

    def __copy_mail_file(self, mail: MailMessage) -> Union[str, None]:
        org_full_path = mail.full_path
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
        if len(mail.hardlinks) <= 1: # 하드링크 걸린 메일이 아니다.
            shutil.copy2(org_full_path, full_new_file)
        else: # 하드링크가 존재하는 메일이다.
            self.__handle_hardlink(mail, full_new_file)
        self.migration_logging.inc_mail_copy()
        self.migration_logging.inc_disk_write(os.stat(full_new_file).st_size)
        return full_new_file

    def __handle_hardlink(self, mail: MailMessage, full_new_file: str):
        org_full_path = mail.full_path
        if self.move_setting.enable_hardlink is False:
            shutil.copy2(org_full_path, full_new_file)
            return
        try:
            same_eml = self.inode_checker[mail.st_ino]
        except KeyError:
            # 하드링크가 존재하지 않는다.
            shutil.copy2(org_full_path, full_new_file)
            self.inode_checker[mail.st_ino] = full_new_file
            return
        if os.path.exists(same_eml) is True:
            os.link(same_eml, full_new_file)
        else:
            self.logger.error("Error. ")
            shutil.copy2(org_full_path, full_new_file)

    def __make_log_identify(self, user: User = None, message: str = ""):
        log_identify = "company_id=%d(%s)" % (self.company.id, self.company.name)
        if user is not None:
            log_identify += ", user_id=%d" % (user.id,)
        if len(message) > 0:
            log_identify += " : %s" % message
        return log_identify

    def __move_a_file(self, user: User, mail: MailMessage, sqlite: SqliteConnector) -> Tuple[bool, Union[str, None], Union[str, None], MailMigrationResultType]:
        old_full_path = sqlite.get_mail_file_name_in_db(mail.folder_no, mail.uid_no)
        if old_full_path is None:
            self.migration_logging.inc_migration_fail_already_removed()
            return False, None, None, MailMigrationResultType.ALREADY_REMOVED
        org_full_path = mail.full_path
        new_full_path = self.__copy_mail_file(mail)
        if new_full_path is None:
            self.migration_logging.inc_migration_fail_invalid_new_directory()
            self.logger.minor("Fail to create new mail file: %s" % self.__make_log_identify(user))
            return False, None, None, MailMigrationResultType.NOT_EXIST_MOVE_TARGET_DIR
        self.migration_logging.inc_sqlite_update_query()
        result = sqlite.update_mail_path(mail.folder_no, mail.uid_no, new_full_path, old_full_path)
        if result is False:
            os.remove(new_full_path)
            self.migration_logging.inc_migration_fail_sqlite_db_update_fail()
            self.migration_logging.inc_mail_delete_as_fail()
            return False, None, None, MailMigrationResultType.SQLITE_M_BACKUP_DB_UPDATE_FAIL
        else:
            #os.remove(org_full_path)
            sqlite.update_mbackup(mail.folder_no, mail.uid_no, new_full_path)
            self.migration_logging.inc_mail_delete()
            return True, org_full_path, new_full_path, MailMigrationResultType.SUCCESS

    @staticmethod
    def __init_user_statistic(user: User) -> UserMigrationResult:
        return UserMigrationResult(
            id=user.id,
            start_at=datetime.datetime.now(),
            end_at=None,
            name=user.name,
            message_store=user.message_store,
            time_consuming=None,
            n_migration_mail_target=len(user.messages),
            n_migration_mail_success=0,
            n_migration_mail_fail=0,
            result=UserMigrationResultType.SUCCESS,
            mail_migration_result_details=[],
            mail_migration_result_type_classify={},
            time_commit_consuming=None,
            commit_start_at=None,
            commit_end_at=None,
        )

    def __handle_a_user(self, user: User) -> UserMigrationResult:
        user_stat = self.__init_user_statistic(user)
        company = self.company
        old_mails_to_delete: List[str] = []
        user = handle_userdata_if_windows(user, self.setting_provider.report.local_test_data_path)
        self.logger.minor("start user mail transfer: %s" % self.__make_log_identify(user))
        try:
            sqlite_db_file_name = os.path.join(user.message_store, "_mcache.db")
            conn = SqliteConnector(sqlite_db_file_name, company.id, user.id, company.name, readonly=False)
            conn.make_mbackup_conn()
            self.migration_logging.inc_sqlite_db_open()
        except Exception as e:
            self.logger.error("start user mail transfer error: %s, error-message=%s"
                              % (self.__make_log_identify(user), e))
            return user_stat

        for idx, mail in enumerate(user.messages):
            is_success = False
            delete_mail_path = None
            self.migration_logging.inc_migration_try()
            result_type = MailMigrationResultType.UNEXPECTED_ERROR
            new_mail_path = None

            try:
                is_success, delete_mail_path, new_mail_path, result_type = self.__move_a_file(user, mail, conn)
            except Exception as e:
                self.logger.error(
                    "Error. fail in __move_a_file : uid=%d, company_id=%d, mail_uid_no=%d, folder_no=%d, e=%s, trace=\n%s"
                    % (user.id, company.id, mail.uid_no, mail.folder_no, e, str_stack_trace()))

                self.migration_logging.inc_migration_fail_unexpected_error()
            if is_success is True:
                self.migration_logging.inc_migration_success()
                old_mails_to_delete.append(delete_mail_path)
            else:
                self.migration_logging.inc_migration_fail()
            user_stat.update_mail_migration_result(
                MailMigrationResult.builder(mail, result_type, new_mail_path)
            )
        user_stat.commit_start_at = datetime.datetime.now()
        if conn.commit() is True:
            user_stat.commit_end_at = datetime.datetime.now()
            for old_mail in old_mails_to_delete:
                os.remove(old_mail)
        else:
            user_stat.commit_end_at = datetime.datetime.now()
        conn.disconnect()
        user_stat.terminate_user_scan()
        self.migration_logging.inc_sqlite_db_close()
        return user_stat

    def run(self, user_ids: Union[List[int], None] = None) -> CompanyMigrationResult:
        self.logger.info("=====================================================")
        self.logger.info("start company mail transfer: %s" % self.__make_log_identify())
        for idx, user in enumerate(self.company.users):
            if get_stop_flags() is True:
                self.logger.info("Stop mail migration - stop signal detected! : company=%d, remain-users=%d" %
                                 (self.company.id, len(self.company.users) - idx))
                break
            if user_ids is not None and user.id not in user_ids:
                continue
            self.company_stat.update_company_scan_result(
                self.__handle_a_user(user)
            )
        self.company_stat.terminate_company_scan()
        save_company_migration_report_as_json(self.company_stat, self.setting_provider.report.migration_result)
        self.logger.info("=====================================================")
        self.logger.info("end company mail transfer: %s" % self.__make_log_identify())
        self.logger.info("=====================================================")
        return self.company_stat
