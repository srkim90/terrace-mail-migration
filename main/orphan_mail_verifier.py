import gzip
import os
import sqlite3
import sys

sys.path.append("/opt/terrace-mail-migration")
sys.path.append("/opt/terrace-mail-migration/binary/Python-minimum/site-packages")
from main.cmd.command_line_parser import read_scan_options
from main.cmd.scan_command_option_models import ScanCommandOptions
from service.logging_service import LoggingService
from service.pgsql_scaner_service import PostgresqlSqlScanner
from service.property_provider_service import application_container
from utils.utills import get_property, try_bytes_decoding
from dataclasses import dataclass
from typing import List, Dict, Tuple

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class DbNameInfo:
    mail_user_seq: int
    mail_domain_seq: int
    mail_uid: str


@dataclass_json
@dataclass
class SqliteDBMails:
    base_path: str
    absolute_mail_name_dict: Dict[str, str]  ## .eml -> _mcache.db
    mail_name_dict: Dict[str, str]  ## .eml -> _mcache.db
    db_name_dict: Dict[str, DbNameInfo]  ## _mcache.db -> mail_user_seq, mail_domain_seq, mail_uid


def make_mail_list_file_path() -> str:
    property = get_property()
    result_path: str = property["report"]["report-path"]
    last_path = result_path.replace("\\", "/").split("/")[-1]
    result_path = result_path.replace(last_path, "sqlite-mail-list")
    if os.path.exists(result_path) is False:
        os.makedirs(result_path)
    return result_path


def make_mail_list_file_name(depth_1: str):
    return os.path.join(make_mail_list_file_path(), "%s.json.gz" % depth_1)


def save_sqlite_db_mail_list(depth_1: str, mails: SqliteDBMails):
    json_name = make_mail_list_file_name(depth_1)
    json_data: str = SqliteDBMails.to_json(mails, indent=4, ensure_ascii=False)
    with gzip.open(json_name, "wb") as fd:
        fd.write(json_data.encode('utf-8'))
    return


class OrphanMailVerifier:
    pgsql: PostgresqlSqlScanner
    logger: LoggingService = application_container.logger

    def __init__(self) -> None:
        super().__init__()
        option: ScanCommandOptions = read_scan_options()
        self.pgsql = PostgresqlSqlScanner(option)

    def check_report_file_aready_exist(self, depth_1: str):
        f_name = make_mail_list_file_name(depth_1)
        return os.path.exists(f_name)

    def enumerate_mindex(self) -> List[Tuple[SqliteDBMails, str]]:
        property = get_property()["mail"]
        mindex_path: str = property["path"]["mindex-path"]
        depth_1_list = os.listdir(mindex_path)
        for idx, depth_1 in enumerate(depth_1_list):
            path_depth_1 = os.path.join(mindex_path, depth_1)
            if os.path.isdir(path_depth_1) is False:
                continue
            if os.listdir(path_depth_1) is False:
                continue
            if self.check_report_file_aready_exist(depth_1) is True:
                self.logger.info("[%d/%d] SKIP : %s is already exist" % (
                    idx + 1, len(depth_1_list), make_mail_list_file_name(depth_1),))
                continue
            mails_db = SqliteDBMails(base_path=path_depth_1, absolute_mail_name_dict={}, mail_name_dict={},
                                     db_name_dict={})
            for depth_2 in os.listdir(path_depth_1):
                path_depth_2 = os.path.join(path_depth_1, depth_2)
                if os.path.isdir(path_depth_2) is False:
                    continue
                for depth_3 in os.listdir(path_depth_2):
                    path_depth_3 = os.path.join(path_depth_2, depth_3)
                    if os.path.isdir(path_depth_3) is False:
                        continue
                    full_path = os.path.join(path_depth_3, "_mcache.db")
                    if os.path.exists(full_path) is False:
                        continue
                    yield mails_db, full_path
            save_sqlite_db_mail_list(depth_1, mails_db)
            self.logger.info(
                "[%d/%d] OK : %s report created" % (idx + 1, len(depth_1_list), make_mail_list_file_name(depth_1),))

    def __get_mail_all(self, conn, only_name: bool = False) -> List[str]:
        mail_list: List[str] = []
        cur = conn.cursor()
        cur.execute("select full_path from mail_message")
        for row in cur:
            is_charset_ok, full_path, coding = try_bytes_decoding(row[0])
            if is_charset_ok is False:
                continue
            if only_name is True:
                full_path = full_path.replace("\\", "/").split("/")[-1]
            mail_list.append(full_path)
        cur.close()
        return mail_list

    def __db_conn(self, db_path: str, readonly: bool = True):
        try:
            if readonly is True:
                conn = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True)
            else:
                conn = sqlite3.connect('file:%s' % db_path, uri=True)
        except sqlite3.NotSupportedError as e:
            conn = sqlite3.connect('%s' % db_path)
        conn.text_factory = bytes
        return conn

    def __mail_list_up(self, full_path: str):
        result = self.__get_mail_all(self.__db_conn(full_path))
        return result

    def __get_user_data_by_mdb(self, mails_db: SqliteDBMails, full_path: str):
        mail_user_seq, mail_domain_seq, mail_uid = self.pgsql.find_user_by_mcache_path(full_path)
        mails_db.db_name_dict[full_path] = DbNameInfo(mail_user_seq=mail_user_seq, mail_domain_seq=mail_domain_seq,
                                                      mail_uid=mail_uid)

    def run(self):
        for mails_db, full_path in self.enumerate_mindex():
            self.__get_user_data_by_mdb(mails_db, full_path)
            for mail_path in self.__mail_list_up(full_path):
                mails_db.absolute_mail_name_dict[mail_path] = full_path
                eml_name = mail_path.replace("\\", "/").split("/")[-1]
                mails_db.mail_name_dict[eml_name] = full_path


def main():
    e = OrphanMailVerifier()
    e.run()


if __name__ == '__main__':
    main()
