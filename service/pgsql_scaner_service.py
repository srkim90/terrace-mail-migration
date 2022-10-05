import datetime
import logging
import os
import threading
import time
from typing import List, Dict, Union, Set, Tuple

from models.company_models import Company, save_company_as_json
from models.company_scan_statistic_models import ScanStatistic, update_statistic
from models.day_models import Days
from models.mail_models import MailMessage
from models.user_models import User
from service.logging_service import LoggingService
from service.pgsql_connector_service import PostgresqlConnector
from service.property_provider_service import ApplicationSettings, ApplicationContainer, ReportSettings
from service.sqlite_connector_service import SqliteConnector
from utils.utills import make_data_file_path, is_windows


class PostgresqlSqlScanner:
    logger: LoggingService = ApplicationContainer().logger()
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()
    mail_checker = ApplicationContainer().mail_file_checker()
    is_windows: bool

    def __init__(self) -> None:
        super().__init__()
        self.report: ReportSettings = self.setting_provider.report
        self.logger.info("PostgresqlScanner start up")
        self.pg_conn = None
        self.is_windows = is_windows()
        self.work_queue: Union[List[Tuple[Company, int]], None] = None
        self.lock = threading.Semaphore(1)

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
            #conn.disconnect()
            return result
        except Exception as e:
            self.logger.error("Error. fail in postgresql query job: %s" % (e,))
            exit()

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
        existing_users: List[User] = []
        for user in company.users:
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
            existing_users.append(user)

            self.logger.minor("company: %s, user: %s, login_id: %s, mail-count: %d, mail-size: %d" % (
                company.name, user.name, user.login_id, user.user_mail_count, user.user_mail_size))
            if user.user_mail_count == 0:
                company.empty_mail_box_user_count += 1
                continue

            # step2 : sqlite DB에서 각 사용자의 메일 목록 리스트업 한다.
            messages: List[MailMessage] = self.__mail_source_path_filter(user, sqlite.get_target_mail_list(days))
            user.user_mail_count = len(messages) # 타겟 경로 검사기능떄문에, 필터링 된 결과로 다시 계산 해줘야 한다.
            user.user_mail_size = 0
            for item in messages:
                # step3 : 이메일 파일 하나하나 메타데이터 읽어 작성하는 메일 리스트에 업데이트 해준다.
                item.st_ctime, item.st_ino, item.st_size = self.__check_eml_data(item)
                company.company_mail_size += item.st_size
                user.user_mail_size_in_db += item.st_size
                user.user_mail_size += item.msg_size
            user.messages = messages

            company.source_path_not_match_mails += user.source_path_not_match_mails
            company.company_mail_count += user.user_mail_count
            company.company_mail_size_in_db += user.user_mail_size

        company.users = existing_users

        return company

    # inode 정보를 업데이트 해서 하드 링크여부를 파악한다.
    def __add_mail_inode_info(self, company: Company) -> Company:
        node_dict: Dict[int, List[MailMessage]] = {}
        for user in company.users:
            for mail in user.messages:
                inode = mail.st_ino
                try:
                    node_dict[inode].append(mail)
                except KeyError:
                    node_dict[inode] = [mail]
                for other_mail in node_dict[inode]:
                    if other_mail.full_path not in mail.hardlinks:
                        mail.hardlinks.append(other_mail.full_path)
                mail.hardlink_count = len(mail.hardlinks)
        #company객체에 통계 정보를 업데이트 해준다.
        for inode in node_dict.keys():
            for idx, mail in enumerate(node_dict[inode]):
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

    def get_users_count(self):
        query = "select count(*) from go_users where company_id in (select id from go_companies)"
        for row in self.__execute_query(query):
            return row[0]

    def __wait_for_processing(self):
        while True:
            time.sleep(0.5)
            self.lock.acquire()
            if len(self.work_queue) == 0:
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

    def __company_worker_th(self, days: Days, company_counts: int, stat: ScanStatistic):
        # self.work_queue 에서 하나를 빼와서 처리한다. self.work_queue가 None이면 종료 한다.
        # 큐가 비었으면, 쉰다.
        while True:
            val = self.__dequeue()
            if val is None:
                return
            company, idx = val
            start: float = time.time()
            json_file_name = None
            company = self.__add_mail_count_info(company, days)
            company = self.__add_mail_inode_info(company)
            if len(company.users) != 0:
                json_file_name = save_company_as_json(company, self.report.report_path)
            self.logger.a_company_complete_logging(idx + 1, company_counts, company, json_file_name, start)
            update_statistic(stat, company)

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



    def report_user_and_company(self, days: Days, company_id: int = -1):
        user_counts = self.get_users_count()
        company_counts = self.get_companies_count()
        end_day = self.setting_provider.date_range.end_day.strftime("%Y-%m-%d")
        start_day = self.setting_provider.date_range.start_day.strftime("%Y-%m-%d")
        stat: ScanStatistic = ScanStatistic.get_empty_statistic(self.setting_provider.date_range.end_day, self.setting_provider.date_range.start_day)

        self.logger.companies_scan_start_up_logging(end_day, start_day, user_counts, company_counts)
        h_threads = self.__make_worker_ths(days, company_counts, stat)
        for idx, company in enumerate(self.find_company(days, company_id)):
            self.__enqueue(company, idx)
        self.__wait_for_processing()
        for h_thread in h_threads:
            h_thread.join()
        stat.scan_end_at = datetime.datetime.now()
        self.logger.companies_scan_complete_logging(stat)

    def find_company(self, days: Days, company_id: int = -1) -> List[Company]:
        where = ""
        if company_id >= 0:
            where = " where id = %d" % (company_id,)
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
                empty_mail_box_user_count=0
            )

            company.users = self.find_users(company)
            companies.append(company)
            yield company

        return companies
