import logging
import os
import platform
import shutil
from typing import Union

from models.company_models import Company, load_company_from_json
from models.mail_models import MailMessage
from models.user_models import User
from service.property_provider_service import ApplicationSettings, ApplicationContainer, ReportSettings, \
    MailMoveSettings
from service.sqlite_connector_service import SqliteConnector
from utils.utills import make_data_file_path

log = logging.getLogger(__name__)


class MailTransferService:
    company: Company
    report_file_name: str
    is_window: Union[bool, None]
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()

    def __init__(self, report_file_name: str) -> None:
        super().__init__()
        self.report_file_name = report_file_name
        self.move_setting: MailMoveSettings = self.setting_provider.move_setting
        self.company = load_company_from_json(report_file_name)
        self.is_window = None
        self.dir_separator = "\\" if self.__is_windows() else "/"

    def __is_windows(self) -> bool:
        if self.is_window is not None:
            return self.is_window
        self.is_window = "window" in platform.system().lower()
        return self.is_window

    def __copy_mail_file(self, org_full_path: str) -> Union[str, None]:
        if self.move_setting.origin_mdata_path not in org_full_path:
            log.error("application.yml 파일에 지정 된 원본 파일 위치와 입력된 파일의 위치가 다릅니다 : org_full_path=%s, %s" %
                      (org_full_path, self.__make_log_identify()))
            return None
        elif os.path.exists(self.move_setting.new_mdata_path) is False or os.path.isdir(self.move_setting.new_mdata_path) is False:
            log.error("이동 대상 디렉토리가 존재하지 않거나, 유효하지 않습니다. : new_mdata_path=%s, %s" %
                      (self.move_setting.new_mdata_path, self.__make_log_identify()))
            return None
        file_name = org_full_path.split(self.dir_separator)[-1]
        new_dir = org_full_path.replace(self.move_setting.origin_mdata_path, "").replace(file_name, "").strip()
        new_dir = os.path.join(self.move_setting.new_mdata_path, new_dir)
        if os.path.exists(new_dir) is False:
            os.makedirs(new_dir)
        full_new_file = os.path.join(new_dir, file_name)
        if os.path.exists(full_new_file) is True:
            log.error("메일 이동 대상 경로에 이미 다른 파일이 존재합니다. : full_new_file=%s, %s" %
                      (full_new_file, self.__make_log_identify()))
            return None
        shutil.copy2(org_full_path, full_new_file)
        return full_new_file

    def __make_log_identify(self, user: User = None, message: str = ""):
        log_identify = "company_id=%d(%s)" % (self.company.id, self.company.name)
        if user is not None:
            log_identify += ", user_id=%d" % (user.id,)
        if len(message) > 0:
            log_identify += " : %s" % message
        return log_identify

    def __move_a_file(self, user: User, mail: MailMessage, sqlite: SqliteConnector) -> bool:
        org_full_path = mail.full_path
        new_full_path = self.__copy_mail_file(org_full_path)
        if new_full_path is None:
            log.error("Fail to create new mail file: %s", self.__make_log_identify(user))
            return False
        result = sqlite.update_mail_path(mail.folder_no, mail.uid_no, new_full_path)
        if result is False:
            os.remove(new_full_path)
        else:
            os.remove(org_full_path)
        return True

    def __handle_a_user(self, user: User) -> bool:
        company = self.company
        log.info("start user mail transfer: %s", self.__make_log_identify(user))
        try:
            sqlite = SqliteConnector(make_data_file_path(user.message_store, ["_mcache.db"]), company.id, user.id, company.name, readonly=False)
        except FileNotFoundError as e:
            log.info("start user mail transfer error: %s", self.__make_log_identify(user))
            return False

        for idx, mail in enumerate(user.messages):
            self.__move_a_file(user, mail, sqlite)
        return True

    def run(self):
        log.info("=====================================================")
        log.info("start company mail transfer: %s", self.__make_log_identify())
        for idx, user in enumerate(self.company.users):
            self.__handle_a_user(user)
        log.info("=====================================================")
        log.info("end company mail transfer: %s", self.__make_log_identify())
        log.info("=====================================================")