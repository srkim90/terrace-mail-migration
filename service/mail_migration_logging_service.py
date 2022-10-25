import threading
import time
from typing import List, Union, Tuple

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from models.company_global_migration_result_models import CompanyGlobalMigrationResult

g_stop_flags = False


# def get

@dataclass_json
@dataclass
class TransactionStatistic:
    def __init__(self) -> None:
        super().__init__()
        self.reset()

    mail_copy: int
    mail_delete: int
    mail_delete_as_fail: int
    sqlite_select_query: int
    sqlite_update_query: int
    sqlite_db_open: int
    sqlite_db_close: int
    make_directory: int
    handle_company: int
    handle_user: int
    disk_write: int
    migration_success: int
    migration_try: int
    migration_fail: int
    migration_fail_already_removed: int
    migration_fail_invalid_new_directory: int
    migration_fail_sqlite_db_update_fail: int
    migration_fail_unexpected_error: int

    def reset(self):
        self.mail_copy = 0
        self.mail_delete = 0
        self.sqlite_select_query = 0
        self.sqlite_update_query = 0
        self.sqlite_db_open = 0
        self.sqlite_db_close = 0
        self.make_directory = 0
        self.handle_company = 0
        self.handle_user = 0
        self.disk_write = 0
        self.mail_delete_as_fail = 0
        self.migration_try = 0
        self.migration_success = 0
        self.migration_fail = 0
        self.migration_fail_already_removed = 0
        self.migration_fail_invalid_new_directory = 0
        self.migration_fail_sqlite_db_update_fail = 0
        self.migration_fail_unexpected_error = 0

    def get_disk_write_as_unit(self) -> str:
        io = self.disk_write
        if io >= 1000 * 1024:
            return "%0.2fMB" % (float(io) / float(1024 * 1024),)
        elif io >= 1000:
            return "%0.2fKB" % (float(io) / float(1024),)
        return "%dB" % (io,)


class MailMigrationLoggingService:
    stat_permanent = TransactionStatistic()
    stat_10sec: TransactionStatistic = TransactionStatistic()
    stat_60sec: TransactionStatistic = TransactionStatistic()
    stat_300sec: TransactionStatistic = TransactionStatistic()
    stat_600sec: TransactionStatistic = TransactionStatistic()
    logger = None

    def __init__(self) -> None:
        super().__init__()

        now_time = time.time()
        self.lock = threading.Semaphore(1)
        self.stats: List[List[TransactionStatistic, Union[int, None], int]] = [
            [self.stat_permanent, None, now_time],
            [self.stat_10sec, 10, now_time],
            [self.stat_60sec, 60, now_time],
            [self.stat_300sec, 300, now_time],
            [self.stat_600sec, 600, now_time],
        ]

    def start_stat(self):
        h_thread = threading.Thread(target=self.__stat_idle_proc)
        h_thread.daemon = True
        h_thread.start()

    def logging(self, log_str):
        if self.logger is None:
            from service.logging_service import LoggingService
            from service.property_provider_service import application_container
            self.logger: LoggingService = application_container.logger
        self.logger.info(log_str)

    def __get_stat_by_duration(self, duration) -> Union[TransactionStatistic, None]:
        for stat_pair in self.stats:
            stat_pair: List[TransactionStatistic, Union[int, None], int]
            stat: TransactionStatistic = stat_pair[0]
            now_duration: Union[int, None] = stat_pair[1]
            if now_duration == duration:
                return stat
        return None

    def __print_log(self) -> None:
        stat = self.__get_stat_by_duration(10)
        self.lock.acquire()
        log_string = \
            "TPS : try=%d, success=%d, fail=%d(%d,%d,%d,%d), mail_copy=%d, mail_delete=%d(%d), sqlite_select_query=%d, " \
            "sqlite_update_query=%d, sqlite_db_open=%d, sqlite_db_close=%d, make_directory=%d, handle_company=%d, " \
            "handle_user=%d, disk_write=%s" \
            % (stat.migration_try, stat.migration_success, stat.migration_fail,
               stat.migration_fail_already_removed,
               stat.migration_fail_invalid_new_directory,
               stat.migration_fail_sqlite_db_update_fail,
               stat.migration_fail_unexpected_error,
               stat.mail_copy, stat.mail_delete,
               stat.mail_delete_as_fail, stat.sqlite_select_query, stat.sqlite_update_query,
               stat.sqlite_db_open, stat.sqlite_db_close, stat.make_directory, stat.handle_company,
               stat.handle_user, stat.get_disk_write_as_unit())
        self.lock.release()
        self.logging(log_string)

    def __stat_idle_proc(self):
        print_duration = 10
        last_display_time = time.time()
        while g_stop_flags is False:
            time.sleep(0.5)
            now_time = time.time()
            for stat_pair in self.stats:
                stat: TransactionStatistic = stat_pair[0]
                duration: Union[int, None] = stat_pair[1]
                last_reset_time: Union[int, None] = stat_pair[2]
                if duration is not None:
                    if now_time >= duration + last_reset_time:
                        if duration == 10:
                            self.__print_log()
                        self.lock.acquire()
                        stat.reset()
                        stat_pair[2] = now_time
                        self.lock.release()
            #if now_time >= print_duration + last_display_time:
            #    self.__print_log()
            #    last_display_time = now_time

    def __inc_stat(self, attr_name: str, value=None) -> None:
        self.lock.acquire()
        try:
            for stat_pair in self.stats:
                stat: TransactionStatistic = stat_pair[0]
                if value is None:
                    __value = getattr(stat, attr_name) + 1
                else:
                    __value = getattr(stat, attr_name) + value
                setattr(stat, attr_name, __value)
        except Exception as e:
            pass
        self.lock.release()

    def inc_migration_try(self):
        self.__inc_stat("migration_try")

    def inc_mail_delete_as_fail(self):
        self.__inc_stat("mail_delete_as_fail")

    def inc_migration_success(self):
        self.__inc_stat("migration_success")

    def inc_migration_fail(self):
        self.__inc_stat("migration_fail")

    def inc_migration_fail_already_removed(self):
        self.__inc_stat("migration_fail_already_removed")

    def inc_migration_fail_invalid_new_directory(self):
        self.__inc_stat("migration_fail_invalid_new_directory")

    def inc_migration_fail_sqlite_db_update_fail(self):
        self.__inc_stat("migration_fail_sqlite_db_update_fail")

    def inc_migration_fail_unexpected_error(self):
        self.__inc_stat("migration_fail_unexpected_error")

    def inc_disk_write(self, value):
        self.__inc_stat("disk_write", value)

    def inc_mail_copy(self):
        self.__inc_stat("mail_copy")

    def inc_mail_delete(self):
        self.__inc_stat("mail_delete")

    def inc_sqlite_select_query(self):
        self.__inc_stat("sqlite_select_query")

    def inc_sqlite_update_query(self):
        self.__inc_stat("sqlite_update_query")

    def inc_sqlite_db_open(self):
        self.__inc_stat("sqlite_db_open")

    def inc_sqlite_db_close(self):
        self.__inc_stat("sqlite_db_close")

    def inc_make_directory(self):
        self.__inc_stat("make_directory")

    def inc_handle_company(self):
        self.__inc_stat("handle_company")

    def inc_handle_user(self):
        self.__inc_stat("handle_user")
