import datetime
import json
import os
import threading
import time
from enum import Enum
from typing import Union

from models.company_models import Company
from models.company_scan_statistic_models import ScanStatistic
from utils.utills import get_property, parser_dir_list


class LogLevel(Enum):
    DEBUG = 0
    MINOR = 1
    INFO = 2
    ERROR = 3

    @staticmethod
    def convertLogLevel(strLogLevel: str):
        levels = [LogLevel.DEBUG, LogLevel.MINOR, LogLevel.INFO, LogLevel.ERROR]
        for item in levels:
            if strLogLevel.upper() == item.name:
                return item
        return None


class LoggingSettings:
    property = get_property()["logging"]
    log_path: str = property["log-path"]
    file_log_level: LogLevel = LogLevel.convertLogLevel(property["file-log-level"])
    stdout_log_level: LogLevel = LogLevel.convertLogLevel(property["stdout-log-level"])
    max_logfile_size: int = int(property["max-logfile-size"]) * (1024 * 1024)
    #max_logfile_count: int = int(property["max-logfile-count"])


class Colors(Enum):
    CEND = '\33[0m'
    CBOLD = '\33[1m'
    CITALIC = '\33[3m'
    CURL = '\33[4m'
    CBLINK = '\33[5m'
    CBLINK2 = '\33[6m'
    CSELECTED = '\33[7m'

    CBLACK = '\33[30m'
    CRED = '\33[31m'
    CGREEN = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE = '\33[36m'
    CWHITE = '\33[37m'

    CBLACKBG = '\33[40m'
    CREDBG = '\33[41m'
    CGREENBG = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG = '\33[46m'
    CWHITEBG = '\33[47m'

    CGREY = '\33[90m'
    CRED2 = '\33[91m'
    CGREEN2 = '\33[92m'
    CYELLOW2 = '\33[93m'
    CBLUE2 = '\33[94m'
    CVIOLET2 = '\33[95m'
    CBEIGE2 = '\33[96m'
    CWHITE2 = '\33[97m'

    CGREYBG = '\33[100m'
    CREDBG2 = '\33[101m'
    CGREENBG2 = '\33[102m'
    CYELLOWBG2 = '\33[103m'
    CBLUEBG2 = '\33[104m'
    CVIOLETBG2 = '\33[105m'
    CBEIGEBG2 = '\33[106m'
    CWHITEBG2 = '\33[107m'

    @staticmethod
    def debug_color(lv: LogLevel):
        if lv == LogLevel.DEBUG:
            return Colors.CWHITE
        elif lv == LogLevel.MINOR:
            return Colors.CGREEN
        elif lv == LogLevel.INFO:
            return Colors.CYELLOW
        elif lv == LogLevel.ERROR:
            return Colors.CRED


lock = threading.Semaphore(1)


class LoggingBase:
    settings: LoggingSettings = LoggingSettings()

    def __init__(self):
        pass

    def debug(self, log_message: str) -> None:
        self.write_log(log_message, LogLevel.DEBUG)

    def minor(self, log_message: str) -> None:
        self.write_log(log_message, LogLevel.MINOR)

    def info(self, log_message: str) -> None:
        self.write_log(log_message, LogLevel.INFO)

    def error(self, log_message: str) -> None:
        self.write_log(log_message, LogLevel.ERROR)

    def __make_log_file_name(self) -> Union[str, None]:
        max_logfile_size = self.settings.max_logfile_size
        log_path = self.settings.log_path
        if os.path.exists(log_path) is False:
            os.makedirs(log_path)
            return None
        file_name = "%s.log" % (datetime.datetime.now().strftime("%Y%m%d"),)
        file_name = os.path.join(log_path,  file_name)
        if os.path.exists(file_name) is True:
            log_status: os.stat_result = os.stat(file_name)
            if max_logfile_size is not None and log_status.st_size > max_logfile_size:
                return None
        return file_name

    def write_log(self, log_message: str, level: LogLevel) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_log_message = "[%s] %s : %s" % (timestamp, level.name, log_message)
        ptr_log_message = "[%s] %s%-5s%s : %s" % (
            timestamp, Colors.debug_color(level).value, level.name, Colors.CEND.value, log_message)
        if self.settings.stdout_log_level.value <= level.value:
            lock.acquire()
            print(ptr_log_message)
            lock.release()
        if self.settings.file_log_level.value <= level.value:
            lock.acquire()
            f_name = self.__make_log_file_name()
            if f_name is not None:
                with open(f_name, "ab") as fd:
                    fd.write(new_log_message.encode("utf-8") + b"\n")
            lock.release()

logger = LoggingBase()


class LoggingService:

    def __init__(self):
        pass

    def debug(self, log_message: str) -> None:
        logger.debug(log_message)

    def minor(self, log_message: str) -> None:
        logger.minor(log_message)

    def info(self, log_message: str) -> None:
        logger.info(log_message)

    def error(self, log_message: str) -> None:
        logger.error(log_message)

    def a_company_complete_logging(self, idx: int, company_counts: int, company: Company, json_file_name: str, start_time: float):
        time_consumed = time.time() - start_time
        report_count = len(company.users)
        report = "[%d/%d] Company scan completed : company_id=%d, name=%s, user_count=%d, mail_count=%d, mail_size=%0.2f(MB), time_consumed=%0.2f(sec), report_file=%s" \
                 % (idx, company_counts, company.id, company.name, report_count, company.company_mail_count,
                    company.company_mail_size / (1024 * 1024), time_consumed, json_file_name)
        self.info(report)
        if company.not_exist_user_in_pgsql > 0:
            self.minor("    -> count of not exist user in pgsql : %d" % (company.not_exist_user_in_pgsql,))
        if company.not_exist_user_in_sqlite > 0:
            self.minor("    -> count of not exist sqlite db file : %d" % (company.not_exist_user_in_sqlite,))
        if report_count == 0:
            self.minor("    -> Empty company, skip report")

    def companies_scan_start_up_logging(self, end_day: str, start_day: str, user_counts: int, company_counts: int):
        prop: dict = get_property()
        prop["mail"]["path"]["origin-mdata-path"] = parser_dir_list(prop["mail"]["path"]["origin-mdata-path"])
        prop["mail"]["path"]["new-mdata-path"] = parser_dir_list(prop["mail"]["path"]["new-mdata-path"])
        del(prop["date-range"])
        setting_json = json.dumps(prop, indent=4, ensure_ascii=False)
        self.info("====== START SCAN FOR MAIL DATA MIGRATION ======")
        self.info("------------------------------------------------")
        self.info(" [Preview]")
        self.info("    - target company counts        : %d" % company_counts)
        self.info("    - target user counts           : %d" % user_counts)
        self.info("    - scan date range              : %s ~ %s" % (start_day, end_day))
        self.info("------------------------------------------------")
        self.info(" [Settings]")
        self.info("%s" % (setting_json,))
        self.info("------------------------------------------------")

    def companies_scan_complete_logging(self, stat: ScanStatistic):
        self.info("====== END SCAN FOR MAIL DATA MIGRATION ======")
        self.info("------------------------------------------------")
        self.info(" [Time]")
        self.info("    - scan start date              : %s" % stat.scan_start_at.strftime("%Y-%m-%d %H:%M:%S"))
        self.info("    - scan end date                : %s" % stat.scan_end_at.strftime("%Y-%m-%d %H:%M:%S"))
        self.info("    - scan time consume            : %d sec" % (stat.scan_end_at - stat.scan_start_at).seconds)
        self.info("------------------------------------------------")
        self.info(" [Mail]")
        self.info("    - company_mail_count           : %s" % stat.company_mail_count)
        self.info("    - source_path_not_match_mails  : %s" % stat.source_path_not_match_mails)
        self.info("    - company_mail_size            : %0.2f MB" % (stat.company_mail_size / (1024 * 1024)))
        self.info("------------------------------------------------")
        self.info(" [Users]")
        self.info("    - available_user_count         : %s" % stat.available_user_count)
        self.info("    - empty_mail_box_user_count    : %s" % stat.empty_mail_box_user_count)
        self.info("    - not_exist_user_in_pgsql      : %s" % stat.not_exist_user_in_pgsql)
        self.info("    - not_exist_user_in_sqlite     : %s" % stat.not_exist_user_in_sqlite)
        self.info("------------------------------------------------")
        self.info(" [Hard-Link]")
        self.info("    - hardlink_mail_count          : %s" % stat.company_hardlink_mail_count)
        self.info("    - non_link_mail_count          : %s" % stat.company_non_link_mail_count)
        self.info("    - mail_unique_count            : %s" % stat.company_hardlink_mail_unique_count)
        self.info("    - hardlink_mail_size           : %0.2f MB" % (stat.company_hardlink_mail_size / (1024 * 1024)))
        self.info("    - non_link_mail_size           : %0.2f MB" % (stat.company_non_link_mail_size / (1024 * 1024)))
        self.info("    - hardlink_mail_unique_size    : %0.2f MB" % (stat.company_hardlink_mail_unique_size / (1024 * 1024)))
        self.info("------------------------------------------------")
