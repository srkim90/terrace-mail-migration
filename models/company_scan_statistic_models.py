import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Union

from dataclasses_json import dataclass_json, config
from marshmallow import fields

from models.company_models import Company
from models.day_models import Days
from utils.utills import get_property, parser_dir_list


@dataclass_json
@dataclass
class ScanStatistic:
    # counting_date_range: Union[Days, None]
    scan_start_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    scan_end_at: Union[datetime, None] = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    scan_start_date: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    scan_end_date: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))

    company_mail_size_in_db: int  # SQLite DB에 집계된 사용자 메일 용량의 합계 (실 파일 사이즈랑 간혹 다르다)
    company_mail_size: int  # A : 회사의 총 메일 용량 (G+H)
    company_mail_count: int  # B : 회사의 총 메일 개수 (C+D)
    company_hardlink_mail_count: int  # C : 회사의 하드 링크가 있는 메일 개수
    company_non_link_mail_count: int  # D : 회사의 하드 링크가 없는 메일 개수
    company_hardlink_mail_unique_count: int  # E : 회사의 하드 링크가 있는 메일 중 중복 되는것을 제외한 개수
    company_hardlink_mail_size: int  # F : 회사의 하드 링크가 있는 메일의 중복을 포함한 용량
    company_non_link_mail_size: int  # G : 회사의 하드 링크가 없는 메일의 용량
    company_hardlink_mail_unique_size: int  # H : 회사의 하드 링크가 있는 메일의 중복을 제외한 용량
    not_exist_user_in_pgsql: int
    not_exist_user_in_sqlite: int
    available_user_count: int
    empty_mail_box_user_count: int
    source_path_not_match_mails: int
    company_count: int
    available_company_count: int
    user_all_mail_count: int
    user_all_mail_size: int
    report_save_path: str
    log_file_names: List[str]
    settings: dict

    def add_logfile_name(self, log_file_name: str) -> None:
        if log_file_name is None:
            return
        if log_file_name not in self.log_file_names:
            self.log_file_names.append(log_file_name)

    @staticmethod
    def get_empty_statistic(scan_end_date: datetime, scan_start_date: datetime, report_save_path: str):
        log_file_names: List[str] = []
        return ScanStatistic(
            # counting_date_range=None,
            scan_start_at=datetime.now(),
            scan_end_at=None,
            company_mail_size_in_db=0,
            company_mail_size=0,
            company_mail_count=0,
            company_hardlink_mail_count=0,
            company_non_link_mail_count=0,
            company_hardlink_mail_unique_count=0,
            company_hardlink_mail_size=0,
            company_non_link_mail_size=0,
            company_hardlink_mail_unique_size=0,
            not_exist_user_in_pgsql=0,
            not_exist_user_in_sqlite=0,
            available_user_count=0,
            empty_mail_box_user_count=0,
            source_path_not_match_mails=0,
            company_count=0,
            available_company_count=0,
            scan_end_date=scan_end_date,
            scan_start_date=scan_start_date,
            user_all_mail_count=0,
            user_all_mail_size=0,
            report_save_path=report_save_path,
            log_file_names=log_file_names,
            settings={}
        )


def merge_scan_stat(stat_a: ScanStatistic, stat_b: ScanStatistic):
    new_stat = ScanStatistic(
        scan_start_at=stat_a.scan_start_at,
        scan_end_at=stat_a.scan_end_at,
        scan_start_date=stat_a.scan_start_date,
        scan_end_date=stat_a.scan_end_date,
        company_mail_size_in_db=stat_a.company_mail_size_in_db + stat_b.company_mail_size_in_db,
        company_mail_size=stat_a.company_mail_size + stat_b.company_mail_size,
        company_mail_count=stat_a.company_mail_count + stat_b.company_mail_count,
        company_hardlink_mail_count=stat_a.company_hardlink_mail_count + stat_b.company_hardlink_mail_count,
        company_non_link_mail_count=stat_a.company_non_link_mail_count + stat_b.company_non_link_mail_count,
        company_hardlink_mail_unique_count=stat_a.company_hardlink_mail_unique_count + stat_b.company_hardlink_mail_unique_count,
        company_hardlink_mail_size=stat_a.company_hardlink_mail_size + stat_b.company_hardlink_mail_size,
        company_non_link_mail_size=stat_a.company_non_link_mail_size + stat_b.company_non_link_mail_size,
        company_hardlink_mail_unique_size=stat_a.company_hardlink_mail_unique_size + stat_b.company_hardlink_mail_unique_size,
        not_exist_user_in_pgsql=stat_a.not_exist_user_in_pgsql + stat_b.not_exist_user_in_pgsql,
        not_exist_user_in_sqlite=stat_a.not_exist_user_in_sqlite + stat_b.not_exist_user_in_sqlite,
        available_user_count=stat_a.available_user_count + stat_b.available_user_count,
        empty_mail_box_user_count=stat_a.empty_mail_box_user_count + stat_b.empty_mail_box_user_count,
        source_path_not_match_mails=stat_a.source_path_not_match_mails + stat_b.source_path_not_match_mails,
        company_count=stat_a.company_count + stat_b.company_count,
        available_company_count=stat_a.available_company_count + stat_b.available_company_count,
        user_all_mail_count=stat_a.user_all_mail_count + stat_b.user_all_mail_count,
        user_all_mail_size=stat_a.user_all_mail_size + stat_b.user_all_mail_size,
        report_save_path=stat_a.report_save_path,
        log_file_names=stat_a.log_file_names,
        settings=stat_a.settings
    )
    return new_stat


def update_statistic(stat: ScanStatistic, company: Company):
    stat.company_mail_size_in_db += company.company_mail_size_in_db
    stat.company_mail_size += company.company_mail_size
    stat.company_mail_count += company.company_mail_count
    stat.company_hardlink_mail_count += company.company_hardlink_mail_count
    stat.company_non_link_mail_count += company.company_non_link_mail_count
    stat.company_hardlink_mail_unique_count += company.company_hardlink_mail_unique_count
    stat.company_hardlink_mail_size += company.company_hardlink_mail_size
    stat.company_non_link_mail_size += company.company_non_link_mail_size
    stat.company_hardlink_mail_unique_size += company.company_hardlink_mail_unique_size
    stat.not_exist_user_in_pgsql += company.not_exist_user_in_pgsql
    stat.not_exist_user_in_sqlite += company.not_exist_user_in_sqlite
    stat.available_user_count += len(company.users)  # - company.empty_mail_box_user_count
    stat.empty_mail_box_user_count += company.empty_mail_box_user_count
    stat.source_path_not_match_mails += company.source_path_not_match_mails
    stat.user_all_mail_count += company.user_all_mail_count
    stat.user_all_mail_size += company.user_all_mail_size
    stat.company_count += 1
    if len(company.users) > 0:
        stat.available_company_count += 1


def get_scan_stat_report_file_name():
    return "scan_statistic_report.json"


def save_scan_stat_as_json(stat: ScanStatistic, save_path: str) -> str:
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    prop: dict = get_property()
    prop["mail"]["path"]["origin-mdata-path"] = parser_dir_list(prop["mail"]["path"]["origin-mdata-path"])
    prop["mail"]["path"]["new-mdata-path"] = parser_dir_list(prop["mail"]["path"]["new-mdata-path"])
    prop["database"]["postgresql"]["password"] = '*' * len(prop["database"]["postgresql"]["password"])
    if "date-range" in prop.keys():
        del (prop["date-range"])
    stat.settings = prop
    file_name = os.path.join(save_path, get_scan_stat_report_file_name())
    json_data = ScanStatistic.to_json(stat, indent=4, ensure_ascii=False).encode("utf-8")
    with open(file_name, "wb") as fd:
        fd.write(json_data)
    return file_name


def load_scan_stat_from_json(json_file_path: str) -> ScanStatistic:
    with open(json_file_path, "rb") as fd:
        return ScanStatistic.from_json(fd.read())
