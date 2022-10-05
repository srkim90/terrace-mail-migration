import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Union

from dataclasses_json import dataclass_json, config
from marshmallow import fields

from models.company_models import Company
from models.day_models import Days
from models.user_models import User


@dataclass_json
@dataclass
class ScanStatistic:
    counting_date_range: Union[Days, None]
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
    company_mail_size_in_db: int             # SQLite DB에 집계된 사용자 메일 용량의 합계 (실 파일 사이즈랑 간혹 다르다)
    company_mail_size: int                   # A : 회사의 총 메일 용량 (G+H)
    company_mail_count: int                  # B : 회사의 총 메일 개수 (C+D)
    company_hardlink_mail_count: int         # C : 회사의 하드 링크가 있는 메일 개수
    company_non_link_mail_count: int         # D : 회사의 하드 링크가 없는 메일 개수
    company_hardlink_mail_unique_count: int  # E : 회사의 하드 링크가 있는 메일 중 중복 되는것을 제외한 개수
    company_hardlink_mail_size: int          # F : 회사의 하드 링크가 있는 메일의 중복을 포함한 용량
    company_non_link_mail_size: int          # G : 회사의 하드 링크가 없는 메일의 용량
    company_hardlink_mail_unique_size: int   # H : 회사의 하드 링크가 있는 메일의 중복을 제외한 용량
    not_exist_user_in_pgsql: int
    not_exist_user_in_sqlite: int
    available_user_count: int
    empty_mail_box_user_count: int

    @staticmethod
    def get_empty_statistic():
        return ScanStatistic(
            counting_date_range=None,
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
            empty_mail_box_user_count=0
        )


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
    stat.available_user_count += len(company.users)
    stat.empty_mail_box_user_count += company.empty_mail_box_user_count
