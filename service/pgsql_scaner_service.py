import datetime
import logging
import os
import threading
import time
from typing import List, Dict, Union, Set, Tuple

from main.cmd.scan_command_option_models import ScanCommandOptions
from models.company_models import Company, save_company_as_json
from models.company_scan_statistic_models import ScanStatistic, update_statistic, save_scan_stat_as_json
from models.day_models import Days
from models.mail_models import MailMessage
from models.user_models import User
from service.logging_service import LoggingService
from service.pgsql_connector_service import PostgresqlConnector
from service.property_provider_service import ApplicationSettings, ReportSettings, application_container
from service.signal_service import get_stop_flags
from service.sqlite_connector_service import SqliteConnector
from utils.utills import make_data_file_path, is_windows, str_stack_trace


class PostgresqlSqlScanner:
    logger: LoggingService = application_container.logger
    setting_provider: ApplicationSettings = application_container.setting_provider
    mail_checker = application_container.mail_file_checker
    is_windows: bool

    def __init__(self, option: ScanCommandOptions) -> None:
        super().__init__()
        self.report: ReportSettings = self.setting_provider.report
        self.logger.info("PostgresqlScanner start up")
        self.pg_conn = None
        self.is_windows = is_windows()
        self.work_queue: Union[List[Tuple[Company, int]], None] = None
        self.lock = threading.Semaphore(1)
        self.report_path = self.__select_report_path(option.scan_data_save_dir)
        self.option: ScanCommandOptions = option

    def __save_user_json(self, user: User, json_full_path: str):
        json_data = User.to_json(user, indent=4, ensure_ascii=False).encode("utf-8")
        with open(json_full_path, "wb") as fd:
            fd.write(json_data)
        return json_full_path

    def __get_user_json_path(self, company: Company, user: User, save: bool) -> str:
        user_json_path = os.path.join(self.report_path, "%d" % (company.id,))
        self.lock.acquire()
        if os.path.exists(user_json_path) is False:
            try:
                os.makedirs(user_json_path)
            except FileExistsError as e:
                pass
        self.lock.release()
        json_full_path = os.path.join(user_json_path, "user_%d.json" % (user.id,))
        if save is True:
            self.__save_user_json(user, json_full_path)
        return json_full_path

    @staticmethod
    def load_user_json_data(json_full_path: str, logger) -> Union[User, None]:
        if type(json_full_path) != str:
            return None
        if os.path.exists(json_full_path) is False:
            logger.error("Error. Cannot find user json file : %s" % (json_full_path,))
            return None
        with open(json_full_path, "rb") as fd:
            return User.from_json(fd.read())

    def __select_report_path(self, report_path: Union[str, None]) -> str:
        if type(report_path) is not str:
            report_path = os.path.join(self.report.report_path, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        if "/" not in report_path and "\\" not in report_path:
            report_path = os.path.join(self.report.report_path, report_path)
        if os.path.exists(report_path) is False:
            try:
                os.makedirs(report_path)
            except FileExistsError:
                pass
        return report_path

    def __pg_disconnect(self) -> None:
        if self.pg_conn is None:
            return
        self.pg_conn.disconnect()
        self.pg_conn = None

    def __execute_query(self, query):
        try:
            if self.pg_conn is None:
                conn = PostgresqlConnector()
                self.pg_conn = conn
            else:
                conn = self.pg_conn
            result = conn.execute(query)
            # conn.disconnect()
            return result
        except Exception as e:
            self.logger.error("Error. fail in postgresql query job: %s" % (e,))
            exit()

    def __str_index_xyx(self, mcache_db_path):
        mcache_db_path_new = mcache_db_path.replace("\\", "/")
        mcache_db_path_new = mcache_db_path_new.replace("/_mcache.db", "")
        mindex_x = mcache_db_path_new.split("/")[-3]
        mindex_y = mcache_db_path_new.split("/")[-2]
        mindex_z = mcache_db_path_new.split("/")[-1]
        like_match = "%s/%s/%s" % (mindex_x, mindex_y, mindex_z)
        return like_match

    def get_valid_mcache_db_count(self, mcache_db_list: List[str], valid_user_list: List[int] = None) -> List[str]:
        db_result_dict: Dict[str, int] = {}
        new_mcache_db_list: List[str] = []
        query = "select message_store, mail_user_seq from mail_user"
        for row in self.__execute_query(query):
            mail_user_seq = row[1]
            message_store = row[0]
            if valid_user_list is not None:
                if mail_user_seq not in valid_user_list:
                    continue
            db_result_dict[self.__str_index_xyx(message_store)] = 1

        for mcache_db_path in mcache_db_list:
            like_match = self.__str_index_xyx(mcache_db_path)
            try:
                db_result_dict[like_match] += 1
                new_mcache_db_list.append(mcache_db_path)
            except KeyError as e:
                pass

            #query = "select mail_user_seq from mail_user where message_store like('%%" + like_match + "')"

        return new_mcache_db_list

    def get_mail_user_id_list(self, exclude_orphan: bool = False, exclude_orphan2: bool = False) -> List[int]:
        where = ""
        query = "select mail_user_seq from mail_user "
        if exclude_orphan is True:
            where = "where mail_user_seq in (select mail_user_seq from go_users)"
        if exclude_orphan2 is True:
            where = "where mail_user_seq in (select mail_user_seq from go_users where company_id in " \
                    "(select id from go_companies))"
        query += where
        mail_user_id_list = []
        for row in self.__execute_query(query):
            mail_user_id_list.append(row[0])
        return mail_user_id_list

    def find_mail_users(self, company: Company, mail_user_seq: int, ) -> (str, str):
        if mail_user_seq is None:
            raise NotImplementedError
        query = "select message_store, mail_uid from mail_user where mail_user_seq = %d" % mail_user_seq
        rows = self.__execute_query(query)[0]
        if rows is None or len(rows) != 2:
            self.logger.error("company: %s, mail_user_seq: %d : 존재하지 않습니다." % (company.name, mail_user_seq))
            raise NotImplementedError
        return rows

    def find_users(self, company: Company):
        query = "select id, mail_user_seq, created_at, updated_at, login_id, mail_group, name from go_users where company_id = %d" % (
            company.id)
        users: List[User] = []
        for idx, row in enumerate(self.__execute_query(query)):
            mail_user_seq = row[1]
            try:
                message_store, mail_uid = self.find_mail_users(company, mail_user_seq)
            except NotImplementedError as e:
                self.logger.minor("fail to get user information : %s" % e.__cause__)
                company.not_exist_user_in_pgsql += 1
                continue
            users.append(User(
                id=row[0],
                mail_user_seq=mail_user_seq,
                created_at=row[2],
                updated_at=row[3],
                login_id=row[4],
                mail_group=row[5],
                name=row[6],
                message_store=message_store,
                mail_uid=mail_uid,
                user_mail_count=0,
                user_mail_size=0,
                user_mail_size_in_db=0,
                source_path_not_match_mails=0,
                user_all_mail_count=0,
                user_all_mail_size=0,
                messages=[]
            ))
        return users

    def __make_mindex_path(self, user: User) -> str:
        return make_data_file_path(user.message_store, ["_mcache.db"])

    def __check_eml_data(self, message: MailMessage) -> (float, int, int):
        stat: os.stat_result = self.mail_checker.check_file_status(message.full_path)
        return stat.st_ctime, stat.st_ino, stat.st_size

    def __mail_source_path_filter(self, user: User, messages: List[MailMessage]) -> List[MailMessage]:
        if self.is_windows is True:
            return messages
        new_message: List[MailMessage] = []
        for msg in messages:
            f_checked = False
            for valid_path in self.setting_provider.move_setting.origin_mdata_path:
                if valid_path in msg.full_path:
                    f_checked = True
                    break
            if f_checked is False:
                self.logger.debug("mail path not in origin_mdata_path, skip : %s" % (msg.full_path,))
                user.source_path_not_match_mails += 1
                continue
            new_message.append(msg)
        return new_message

    def __add_mail_count_info(self, company: Company, days: Days) -> Company:
        existing_users: List[str] = []
        for basic_user in company.users:
            user: User = basic_user
            mindex_path = self.__make_mindex_path(user)
            # if os.path.exists(mindex_path) is False:
            #     continue -> 함수안에서 파일 존재 여부 체크 처리
            # step1 : sqlite DB에서 사용자 메일 수 뽑아올린다.
            try:
                sqlite = SqliteConnector(mindex_path, company.id, user.id, company.name)
            except FileNotFoundError as e:
                company.not_exist_user_in_sqlite += 1
                continue
            user.user_mail_count, user.user_mail_size = sqlite.get_target_mail_count(days)
            user.user_all_mail_count, user.user_all_mail_size = sqlite.get_target_mail_count(None)


            self.logger.minor("company: %s, user: %s, login_id: %s, mail-count: %d, mail-size: %d" % (
                company.name, user.name, user.login_id, user.user_mail_count, user.user_mail_size))
            if user.user_mail_count == 0:
                company.empty_mail_box_user_count += 1
                continue

            user_json_name = self.__get_user_json_path(company, user, False)
            existing_users.append(user_json_name)

            # step2 : sqlite DB에서 각 사용자의 메일 목록 리스트업 한다.
            new_messages: List[MailMessage] = []
            messages: List[MailMessage] = self.__mail_source_path_filter(user, sqlite.get_target_mail_list(days))
            user.user_mail_count = len(messages)  # 타겟 경로 검사기능떄문에, 필터링 된 결과로 다시 계산 해줘야 한다.
            user.user_mail_size = 0

            for item in messages:
                # step3 : 이메일 파일 하나하나 메타데이터 읽어 작성하는 메일 리스트에 업데이트 해준다.
                try:
                    item.st_ctime, item.st_ino, item.st_size = self.__check_eml_data(item)
                except Exception as e:
                    self.logger.debug("Error. Fail to check email file status : user-id=%d, file-name=%s, error=%s" %
                                      (user.id, item.full_path, e))
                    continue
                company.company_mail_size += item.st_size
                user.user_mail_size_in_db += item.st_size
                user.user_mail_size += item.msg_size
                new_messages.append(item)
            user.messages = new_messages

            company.source_path_not_match_mails += user.source_path_not_match_mails
            company.company_mail_count += user.user_mail_count
            company.company_mail_size_in_db += user.user_mail_size
            company.user_all_mail_count += user.user_all_mail_count
            company.user_all_mail_size += user.user_all_mail_size

            self.__get_user_json_path(company, user, True)

        company.users = existing_users

        return company

    # inode 정보를 업데이트 해서 하드 링크여부를 파악한다. (company 당 한번 동작)
    def __add_mail_inode_info(self, company: Company) -> Company:
        if self.setting_provider.move_setting.enable_hardlink is False:
            return company
        node_dict: Dict[int, List[MailMessage]] = {}
        for user_path in company.users:
            try:
                user = self.load_user_json_data(user_path, self.logger)
            except Exception as e:
                #self.logger.error("Error in load json_data : %s" % (str_stack_trace(),))
                user = None
            if user is None:
                continue
            # step.1 : 모든 사용자를 대상으로 inode 별 dict을 만든다.
            for mail in user.messages:
                inode = mail.st_ino
                try:
                    node_dict[inode].append(mail)
                except KeyError:
                    node_dict[inode] = [mail]
        for user_path in company.users:
            if type(user_path) == str:
                user = self.load_user_json_data(user_path, self.logger)
            else:
                user = user_path
            if user is None:
                continue
            for mail in user.messages:
                inode = mail.st_ino
                try:
                    k_checker = node_dict[inode]
                except KeyError:
                    continue
                for other_mail in node_dict[inode]: # 각 개별메일에서 하드링크 카운트 및 목록을 업데이트 해준다.
                    if other_mail.full_path not in mail.hardlinks:
                        mail.hardlinks.append(other_mail.full_path)
                mail.hardlink_count = len(mail.hardlinks)
            self.__save_user_json(user, user_path)
        # step.2 : company객체에 통계 정보를 업데이트 해준다.
        for inode in node_dict.keys():
            for idx, mail in enumerate(node_dict[inode]):
                mail.hardlink_count = len(node_dict[inode])
                if mail.hardlink_count >= 2:
                    company.company_hardlink_mail_count += 1
                    company.company_hardlink_mail_size += mail.st_size
                    if idx == 0:
                        company.company_hardlink_mail_unique_count += 1
                        company.company_hardlink_mail_unique_size += mail.st_size
                else:
                    company.company_non_link_mail_count += 1
                    company.company_non_link_mail_size += mail.st_size
        return company

    def get_companies_count(self, company_id: int = -1):
        where = ""
        if company_id >= 0:
            where = " where id = %d" % (company_id,)
        query = "select count(*) from go_companies" + where
        for row in self.__execute_query(query):
            return row[0]

    def get_users_count(self, all_count: bool = False):
        query = "select count(*) from go_users"
        if all_count is False:
            query += ' where company_id in (select id from go_companies)'
        for row in self.__execute_query(query):
            return row[0]

    def __wait_for_processing(self):
        while True:
            time.sleep(0.5)
            self.lock.acquire()
            if len(self.work_queue) == 0 or get_stop_flags() is True:
                self.work_queue = None
                self.lock.release()
                return
            self.lock.release()

    def __enqueue(self, company: Company, idx: int):
        self.lock.acquire()
        self.work_queue.append((company, idx))
        self.lock.release()

    def __dequeue(self) -> Union[Tuple[Company, int], None]:
        while True:
            self.lock.acquire()
            if self.work_queue is None:
                self.lock.release()
                return None
            if len(self.work_queue) == 0:
                self.lock.release()
                time.sleep(0.25)
                continue
            company, idx = self.work_queue[0]
            self.work_queue = self.work_queue[1:]
            self.lock.release()
            return company, idx

    def __company_worker_th(self, days: Days, company_counts: int, stat: ScanStatistic) -> None:
        # self.work_queue 에서 하나를 빼와서 처리한다. self.work_queue가 None이면 종료 한다.
        # 큐가 비었으면, 쉰다.
        while True:
            val = self.__dequeue()
            if val is None or get_stop_flags() is True:
                break
            company, idx = val
            company: Company
            start: float = time.time()
            json_file_name = None
            try:
                company = self.__add_mail_count_info(company, days)
                company = self.__add_mail_inode_info(company)
                if len(company.users) > 0:
                    json_file_name = save_company_as_json(company, self.report_path)
                self.logger.a_company_complete_logging(idx + 1, company_counts, company, json_file_name, start)
                self.lock.acquire()
                update_statistic(stat, company)
                self.lock.release()
            except Exception as e:
                self.logger.error("[__company_worker_th] Error in Scan company : %s\n%s" % (e, str_stack_trace()))
                continue
        return

    def __make_worker_ths(self, days: Days, company_counts: int, stat: ScanStatistic):
        self.work_queue = []
        h_threads: List[threading.Thread] = []
        max_work_threads = self.setting_provider.system.max_work_threads
        for idx in range(max_work_threads):
            h_thread = threading.Thread(target=self.__company_worker_th, args=(days, company_counts, stat))
            h_thread.daemon = True
            h_thread.start()
            h_threads.append(h_thread)
        return h_threads

    def __is_exclude_company(self, company: Company, option: ScanCommandOptions) -> bool:
        if option.exclude_company_ids is None or len(option.exclude_company_ids) is 0:
            return True
        if str(company.id) in option.exclude_company_ids:
            return False
        return True

    def __is_my_rr_index(self, idx: int) -> bool:
        # 멀티 프로세스로 실행 시켰을 경우, 자신의 인덱스 인지 확인한다.
        if type(self.option.rr_index) is not int or type(self.setting_provider.system.max_work_process) is not int:
            return True
        if self.option.rr_index < 0 or self.option.rr_index >= self.setting_provider.system.max_work_process:
            return True
        now_rr_index = idx % self.setting_provider.system.max_work_process
        #print("now_rr_index : %s" % (now_rr_index,))
        if now_rr_index == self.option.rr_index:
            return True
        return False

    def report_user_and_company(self, option: ScanCommandOptions):
        days: Days = option.scan_range
        company_ids: Union[List[int], None] = option.target_company_ids

        end_day = datetime.datetime.now()
        start_day = datetime.datetime.strptime("1975-01-01 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
        user_counts = self.get_users_count()
        company_counts = self.get_companies_count()
        if days is None and is_windows() is True:
            days = self.setting_provider.date_range.date_range
        if days is not None and (days.end_day is not None):
            end_day = days.end_day
            if days.start_day is not None:
                start_day = days.start_day
        stat: ScanStatistic = ScanStatistic.get_empty_statistic(end_day,
                                                                start_day,
                                                                self.report_path)
        stat.add_logfile_name(self.logger.make_log_file_name())

        if self.option.rr_index is None:
            self.logger.companies_scan_start_up_logging(end_day.strftime("%Y-%m-%d"), start_day.strftime("%Y-%m-%d"),
                                                        user_counts, company_counts)
        h_threads = self.__make_worker_ths(days, company_counts, stat)
        for idx, company in enumerate(self.find_company(days, company_ids)):
            if self.__is_my_rr_index(idx) is False:
                continue
            if self.__is_exclude_company(company, option) is True:
                self.__enqueue(company, idx)
            if get_stop_flags() is True:
                break
        self.__wait_for_processing()
        for idx, h_thread in enumerate(h_threads):
            h_thread.join()
            self.logger.info("wait for worker thread terminated : remain thread=[%d/%d]" % (idx, len(h_threads),))
        self.logger.info("end of waiting threads")
        stat.scan_end_at = datetime.datetime.now()
        stat.add_logfile_name(self.logger.make_log_file_name())
        if option.rr_index is None:
            self.logger.companies_scan_complete_logging(stat)
        save_scan_stat_as_json(stat, self.report_path, self.option.rr_index)

    def find_company(self, days: Days, company_ids: Union[List[int], None] = None) -> List[Company]:
        where = ""
        if company_ids is not None:
            where = " where "
            for idx, company_id in enumerate(company_ids):
                if idx != 0:
                    where += " or "
                where += " id = %d" % (company_id,)
        query = "select id, created_at, updated_at, domain_name, name, online_user_count, stop_user_count, user_count, wait_user_count, site_url, uuid, mail_domain_seq, company_group_id, manager_id from go_companies" + where
        companies: List[Company] = []
        for row in self.__execute_query(query):
            company = Company(
                id=row[0],
                counting_date_range=days,
                created_at=row[1],
                updated_at=row[2],
                domain_name=row[3],
                name=row[4],
                online_user_count=row[5],
                stop_user_count=row[6],
                user_count=row[7],
                wait_user_count=row[8],
                site_url=row[9],
                uuid=row[10],
                mail_domain_seq=row[11],
                company_group_id=row[12],
                manager_id=row[13],
                users=[],
                company_mail_size_in_db=0,
                company_mail_count=0,
                company_mail_size=0,
                company_hardlink_mail_count=0,
                company_non_link_mail_count=0,
                company_hardlink_mail_unique_count=0,
                company_hardlink_mail_size=0,
                company_non_link_mail_size=0,
                company_hardlink_mail_unique_size=0,
                not_exist_user_in_pgsql=0,
                not_exist_user_in_sqlite=0,
                source_path_not_match_mails=0,
                empty_mail_box_user_count=0,
                user_all_mail_count=0,
                user_all_mail_size=0
            )

            company.users = self.find_users(company)
            companies.append(company)
            yield company

        return companies
