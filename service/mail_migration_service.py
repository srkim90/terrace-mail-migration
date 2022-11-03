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
from models.mail_remove_models import MailRemoveModels
from models.user_migration_result_models import UserMigrationResult
from models.user_models import User
from service.logging_service import LoggingService
from service.mail_migration_logging_service import MailMigrationLoggingService
from service.property_provider_service import ApplicationSettings, application_container
from service.signal_service import get_stop_flags
from service.sqlite_connector_service import SqliteConnector
from utils.utills import handle_userdata_if_windows, is_windows, str_stack_trace, print_user_info, calc_file_hash


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
            valid_path = valid_path.strip()
            if valid_path[-1] != self.dir_separator:
                valid_path += self.dir_separator
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
        val = self.__select_move_target_dir_in()
        strategy: MoveStrategyType = self.move_setting.move_strategy
        self.logger.debug("__select_move_target_dir: %s, strategy: %s" % (val, strategy.name))
        return val

    def __select_move_target_dir_in(self) -> str:
        threshold_ratio = self.move_setting.partition_capacity_threshold_ratio
        strategy: MoveStrategyType = self.move_setting.move_strategy
        avail_list = []
        idx = 0
        max_idxs: List[int] = []
        min_idxs: List[int] = []
        max_ratio = None
        min_ratio = None
        for path in self.move_setting.new_mdata_path:
            ratio = self.__calc_volume_used_ratio(path)
            if ratio >= threshold_ratio:
                continue
            avail_list.append([ratio, path, ])
            if max_ratio is None or ratio > max_ratio:
                max_idxs = [idx, ]
                max_ratio = ratio
            elif ratio == max_ratio:
                max_idxs.append(idx)
            if min_ratio is None or ratio < min_ratio:
                min_idxs = [idx, ]
                min_ratio = ratio
            elif ratio == min_ratio:
                min_idxs.append(idx)
            idx += 1
        if strategy == MoveStrategyType.RANDOM or strategy == MoveStrategyType.ROUND_ROBIN:
            return avail_list[random.randrange(0, len(avail_list))][1]
        elif strategy == MoveStrategyType.REMAINING_CAPACITY_HIGHER_PRIORITY:
            return avail_list[max_idxs[random.randrange(0, len(max_idxs))]][1]
        elif strategy == MoveStrategyType.REMAINING_CAPACITY_LOWER_PRIORITY:
            return avail_list[min_idxs[random.randrange(0, len(min_idxs))]][1]

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

    def __check_already_moved(self, org_full_path: str):
        # 해당 메일이 이미 이관 되었는지를 확인 한다.
        now_mdata = None
        mail_path = None
        for mdata_path in self.move_setting.origin_mdata_path:
            if mdata_path in org_full_path:
                now_mdata = mdata_path
                mail_path = org_full_path.replace(now_mdata, "")
                if mail_path[0] == self.dir_separator:
                    mail_path = mail_path[1:]
                break
        if now_mdata is None:
            return False
        for mdata_path in self.move_setting.new_mdata_path:
            check_path = os.path.join(mdata_path, mail_path)
            if os.path.exists(check_path) is True:
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

    def __copy_mail_file(self, mail: MailMessage) -> Union[Tuple[MailMigrationResultType, str], Tuple[MailMigrationResultType, None]]:
        org_full_path = mail.full_path
        new_mdata_path = self.__select_move_target_dir()
        if self.__check_origin_mdata_path(org_full_path) is False:
            self.logger.debug("application.yml 파일에 지정 된 원본 파일 위치와 입력된 파일의 위치가 다릅니다. (SKIP) : org_full_path=%s, %s" %
                              (org_full_path, self.__make_log_identify()))
            return MailMigrationResultType.ORIGINAL_DIR_NOT_IN_APPLICATION_YML, None
        elif os.path.exists(org_full_path) is False:
            self.logger.debug("이관할 파일이 존재하지 않습니다. : org_full_path=%s, %s" %
                              (org_full_path, self.__make_log_identify()))
            stat: MailMigrationResultType = MailMigrationResultType.ALREADY_REMOVED if \
                self.__check_already_moved(org_full_path) else  MailMigrationResultType.NOT_EXIST_MAIL_FILE_TO_MOVE
            return stat, None
        elif new_mdata_path is None:
            self.logger.error("이동 대상 디렉토리가 존재하지 않거나, 유효하지 않습니다. : new_mdata_path=%s, %s" %
                              (self.move_setting.new_mdata_path, self.__make_log_identify()))
            return MailMigrationResultType.NOT_EXIST_MOVE_TARGET_DIR, None
        file_name = org_full_path.split(self.dir_separator)[-1]
        select_move_target_dir = self.__select_move_target_dir()
        m_data_subdir = self.__m_data_subdir_parser(org_full_path)
        self.logger.debug("new_mdata_path: %s, select_move_target_dir: %s, m_data_subdir: %s" % (
        new_mdata_path, select_move_target_dir, m_data_subdir))
        new_dir = os.path.join(select_move_target_dir, m_data_subdir)
        new_dir = os.path.join(new_mdata_path, new_dir)
        self.logger.debug("new_dir: %s" % (new_dir,))
        if os.path.exists(new_dir) is False:
            os.makedirs(new_dir)
        full_new_file = os.path.join(new_dir, file_name)
        if os.path.exists(full_new_file) is True:
            self.logger.minor("메일 이동 대상 경로에 이미 다른 파일이 존재합니다. : full_new_file=%s, %s" %
                              (full_new_file, self.__make_log_identify()))
            return MailMigrationResultType.ALREADY_MOVED_AND_REMAIN_OLD_MAIL_FILES, None
        # self.convert_mail_dir_volume_to_same_first_hardlink_test(full_new_file, full_new_file)
        if len(mail.hardlinks) <= 1:  # 하드링크 걸린 메일이 아니다.
            shutil.copy2(org_full_path, full_new_file)
        else:  # 하드링크가 존재하는 메일이다.
            tmp_new_file = self.__handle_hardlink(mail, full_new_file)
            if tmp_new_file is not None:
                full_new_file = tmp_new_file
        self.migration_logging.inc_mail_copy()
        self.migration_logging.inc_disk_write(os.stat(full_new_file).st_size)
        return MailMigrationResultType.SUCCESS, full_new_file

    def __get_move_target_volume_path(self, mail_path: str) -> Union[str, None]:
        for path in self.move_setting.new_mdata_path:
            if len(mail_path) <= len(path):
                continue
            org_path = mail_path[0:len(path)]
            if path == org_path:
                return org_path
        return None

    def convert_mail_dir_volume_to_same_first_hardlink_test(self, same_eml, full_new_file):
        same_eml_volume_path = self.__get_move_target_volume_path(same_eml)
        new_eml_volume_path = self.__get_move_target_volume_path(full_new_file)
        if same_eml_volume_path is None or new_eml_volume_path is None:
            return None
        # if same_eml_volume_path == new_eml_volume_path:
        #    return full_new_file
        full_new_file = full_new_file.replace(new_eml_volume_path, "")
        full_new_file = os.path.join(same_eml_volume_path, full_new_file)
        file_name = full_new_file.split(self.dir_separator)[-1]
        dir_name = full_new_file.replace(file_name, "")
        return

    def __convert_mail_dir_volume_to_same_first_hardlink(self, same_eml, full_new_file) -> Union[str, None]:
        # 하드링크는 동일한 볼륨 내부에만 유효하다.
        # 따라서 하드링크를 걸려는 메일의 파티션을 원본 메일과 동일하게 변경 해준다.
        org_full_new_file = full_new_file
        same_eml_volume_path = self.__get_move_target_volume_path(same_eml)
        new_eml_volume_path = self.__get_move_target_volume_path(full_new_file)
        if same_eml_volume_path is None or new_eml_volume_path is None:
            return None
        if same_eml_volume_path == new_eml_volume_path:
            return full_new_file
        full_new_file = full_new_file.replace(new_eml_volume_path, "")
        if full_new_file[0] == self.dir_separator:
            full_new_file = full_new_file[1:]
        full_new_file = os.path.join(same_eml_volume_path, full_new_file)
        file_name = full_new_file.split(self.dir_separator)[-1]
        dir_name = full_new_file.replace(file_name, "")
        try:
            if os.path.exists(dir_name) is False:
                os.makedirs(dir_name)
        except PermissionError:
            self.logger.error("[__convert_mail_dir_volume_to_same_first_hardlink] same_eml: %s, full_new_file: %s, same_eml_volume_path: %s, new_eml_volume_path: %s, org_full_new_file: %s, file_name: %s, dir_name:%s" %
                  (same_eml, full_new_file, same_eml_volume_path, new_eml_volume_path, org_full_new_file, file_name, dir_name))
            raise PermissionError
        return full_new_file

    def __handle_hardlink(self, mail: MailMessage, full_new_file: str) -> Union[str, None]:
        org_full_path = mail.full_path
        if self.move_setting.enable_hardlink is False:
            shutil.copy2(org_full_path, full_new_file)
            return None
        try:
            same_eml = self.inode_checker[mail.st_ino]
        except KeyError:
            # 하드링크가 존재하지 않는다. (동일 하드링크에 대해 처음 이관 하는 메일이다.)
            shutil.copy2(org_full_path, full_new_file)
            self.inode_checker[mail.st_ino] = full_new_file
            return None
        if os.path.exists(same_eml) is True:
            try:
                hardlink_new_file = self.__convert_mail_dir_volume_to_same_first_hardlink(same_eml, full_new_file)
                os.link(same_eml, hardlink_new_file)
                return hardlink_new_file
            except Exception as e:
                self.logger.error("Error fail to make hardlink, make new file no hardlink: %s" % (str_stack_trace(),))
                shutil.copy2(org_full_path, full_new_file)
                return None
        else:
            self.logger.error("Error fail to make hardlink x2, make new file no hardlink: %s" % (str_stack_trace(),))
            shutil.copy2(org_full_path, full_new_file)
        return None

    def __make_log_identify(self, user: User = None, message: str = ""):
        log_identify = "company_id=%d(%s)" % (self.company.id, self.company.name)
        if user is not None:
            log_identify += ", user_id=%d" % (user.id,)
        if len(message) > 0:
            log_identify += " : %s" % message
        return log_identify

    def __move_a_file(self, user: User, mail: MailMessage, sqlite: SqliteConnector) -> Tuple[
        bool, Union[str, None], Union[str, None], MailMigrationResultType]:
        old_full_path = sqlite.get_mail_file_name_in_db(mail.folder_no, mail.uid_no)
        if old_full_path is None:
            self.migration_logging.inc_migration_fail_already_removed()
            return False, None, None, MailMigrationResultType.ALREADY_REMOVED
        org_full_path = mail.full_path
        stat, new_full_path = self.__copy_mail_file(mail)
        if new_full_path is None:
            self.migration_logging.inc_migration_fail_invalid_new_directory()
            self.logger.minor("Fail to create new mail file: %s" % self.__make_log_identify(user))
            return False, None, None, stat
        self.migration_logging.inc_sqlite_update_query()
        result = sqlite.update_mail_path(mail.folder_no, mail.uid_no, new_full_path, old_full_path)
        if result is False:
            os.remove(new_full_path)
            self.migration_logging.inc_migration_fail_sqlite_db_update_fail()
            self.migration_logging.inc_mail_delete_as_fail()
            return False, None, None, MailMigrationResultType.SQLITE_M_BACKUP_DB_UPDATE_FAIL
        else:
            # os.remove(org_full_path) # commit 이후 삭제하도록 로직을 변경 하였다.
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
        old_mails_to_delete: List[MailRemoveModels] = []
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
                old_mails_to_delete.append(MailRemoveModels(
                    folder_no=mail.folder_no,
                    uid_no=mail.uid_no,
                    del_full_path=delete_mail_path,
                    new_full_path=new_mail_path,
                    msg_size=mail.msg_size
                ))
            else:
                self.migration_logging.inc_migration_fail()
            user_stat.update_mail_migration_result(
                MailMigrationResult.builder(mail, result_type, new_mail_path)
            )
        user_stat.commit_start_at = datetime.datetime.now()
        commit_result = conn.commit()
        conn.disconnect()
        if commit_result is True:
            user_stat.commit_end_at = datetime.datetime.now()
            check_conn = SqliteConnector(sqlite_db_file_name, company.id, user.id, company.name, readonly=True)
            for rm_model in old_mails_to_delete:
                if self.__final_check_and_delete_old_mail(rm_model, check_conn) is False:
                    self.logger.info("Fail to delete mail : %s, del_full_path=%s" % (
                    print_user_info(company, user), rm_model.del_full_path))
            check_conn.disconnect()
        else:
            self.logger.error("Fail to commit : %s" % print_user_info(company, user))
            user_stat.commit_end_at = datetime.datetime.now()

        user_stat.terminate_user_scan()
        self.migration_logging.inc_sqlite_db_close()
        return user_stat

    def __final_check_and_delete_old_mail(self, rm_model: MailRemoveModels, conn: SqliteConnector) -> bool:
        # 1. 존재하는지 확인
        if os.path.exists(rm_model.del_full_path) is False:
            self.logger.error("not exist mail to delete : %s" % (rm_model.del_full_path,))
            return False

        if os.path.exists(rm_model.new_full_path) is False:
            self.logger.error("not exist new mail : %s" % (rm_model.new_full_path,))
            return False

        # 2. DB 경로와 일치하는지 체크
        db_full_path = conn.get_mail_file_name_in_db(rm_model.folder_no, rm_model.uid_no)
        if self.__is_windows() is False:
            if os.path.samefile(db_full_path, rm_model.new_full_path) is False:
                self.logger.error("not compare new mail with db : %s" % (rm_model.new_full_path,))
                return False

        # 3. 제거 하려는 파일과 이관한 파일의 내용이 동일한지 확인 (설정에 따라 cksum, size 지원)
        if self.move_setting.final_check_method.lower() in ["md5sum", "cksum", "checksum"]:
            new_cksum = calc_file_hash(rm_model.new_full_path)
            del_cksum = calc_file_hash(rm_model.del_full_path)
            if new_cksum != del_cksum:
                self.logger.error("not compare checksum between new-mail and old-mail: %s, %s" %
                                  (rm_model.new_full_path, rm_model.del_full_path))
                return False
        elif self.move_setting.final_check_method.lower() in ["none", "null", ]:
            pass
        else:
            new_size = os.stat(rm_model.new_full_path).st_size
            del_size = os.stat(rm_model.del_full_path).st_size
            if new_size != del_size:
                self.logger.error("not compare size between new-mail and old-mail: %s, %s" %
                                  (rm_model.new_full_path, rm_model.del_full_path))
                return False

        # 4. 테스트를 통과 하였다면, 원본 메일을 제거!
        os.remove(rm_model.del_full_path)
        self.logger.debug("delete mail : %s" % (rm_model.del_full_path,))
        return True

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
