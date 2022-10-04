import datetime
import os
import threading
import time
from enum import Enum
from typing import Union

from models.company_models import Company
from utils.utills import get_property


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
    log_path: str = property["log_path"]
    file_log_level: LogLevel = LogLevel.convertLogLevel(property["file_log_level"])
    stdout_log_level: LogLevel = LogLevel.convertLogLevel(property["stdout_log_level"])
    max_logfile_size: int = int(property["max_logfile_size"])
    max_logfile_count: int = int(property["max_logfile_count"])


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
        return None
        max_logfile_size = self.settings.max_logfile_size
        max_logfile_count = self.settings.max_logfile_count
        log_path = self.settings.log_path
        if os.path.exists(log_path) is False:
            return None
        file_name = os.path.join(log_path, "")
        os.stat(file_name)

    def write_log(self, log_message: str, level: LogLevel) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_log_message = "[%s] %s : %s" % (timestamp, level.name, log_message)
        ptr_log_message = "[%s] %s%-5s%s : %s" % (
            timestamp, Colors.debug_color(level).value, level.name, Colors.CEND.value, log_message)
        if self.settings.stdout_log_level.value <= level.value:
            print(ptr_log_message)
        if self.settings.file_log_level.value <= level.value:
            f_name = self.__make_log_file_name()
            if f_name is not None:
                with open(f_name, "ab") as fd:
                    fd.write(new_log_message.encode("utf-8") + b"\n")


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

    def company_logging(self, idx: int, company_counts: int, company: Company, json_file_name: str, start_time: float):
        time_consumed = time.time() - start_time
        report_count = len(company.users)
        report = "[%d/%d] Company scan completed : company_id=%d, name=%s, user_count=%d, mail_count=%d, mail_size=%0.2f(MB), time_consumed=%0.2f(sec), report_file=%s" \
                 % (idx, company_counts, company.id, company.name, report_count, company.company_mail_count,
                    company.company_mail_size / (1024 * 1024), time_consumed, json_file_name)
        self.info(report)
        if company.not_exist_user_in_pgsql > 0:
            self.error("    -> count of not exist user in pgsql : %d" % (company.not_exist_user_in_pgsql,))
        if company.not_exist_user_in_sqlite > 0:
            self.error("    -> count of not exist sqlite db file : %d" % (company.not_exist_user_in_sqlite,))
        if report_count == 0:
            self.minor("    -> Empty company, skip report")
