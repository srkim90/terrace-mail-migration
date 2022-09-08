import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from dataclasses_json import dataclass_json, config
from marshmallow import fields

from models.day_models import Days
from models.user_models import User


@dataclass_json
@dataclass
class Company:
    id: int
    counting_date_range: Days
    created_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    updated_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    domain_name: str
    name: str
    online_user_count: int
    stop_user_count: int
    user_count: int
    wait_user_count: int
    site_url: str
    uuid: str
    mail_domain_seq: int
    company_group_id: int
    manager_id: int
    company_mail_size_in_db: int             # SQLite DB에 집계된 사용자 메일 용량의 합계 (실 파일 사이즈랑 간혹 다르다)
    company_mail_size: int                   # A : 회사의 총 메일 용량 (G+H)
    company_mail_count: int                  # B : 회사의 총 메일 개수 (C+D)
    company_hardlink_mail_count: int         # C : 회사의 하드 링크가 있는 메일 개수
    company_non_link_mail_count: int         # D : 회사의 하드 링크가 없는 메일 개수
    company_hardlink_mail_unique_count: int  # E : 회사의 하드 링크가 있는 메일 중 중복 되는것을 재외한 개수
    company_hardlink_mail_size: int          # F : 회사의 하드 링크가 있는 메일의 중복을 포함한 용량
    company_non_link_mail_size: int          # G : 회사의 하드 링크가 없는 메일의 용량
    company_hardlink_mail_unique_size: int   # H : 회사의 하드 링크가 있는 메일의 중복을 재외한 용량
    users: List[User]


def save_company_as_json(company: Company, save_path: str) -> None:
    file_name = os.path.join(save_path, "company_report_%d_%d_%dMB.json" % (
    company.id, company.company_mail_count, company.company_mail_size / (1024 * 1024)))
    json_data = Company.to_json(company, indent=4, ensure_ascii=False).encode("utf-8")
    with open(file_name, "wb") as fd:
        fd.write(json_data)


def load_company_from_json(json_file_path: str) -> Company:
    with open(json_file_path, "rb") as fd:
        return Company.from_json(fd.read())
