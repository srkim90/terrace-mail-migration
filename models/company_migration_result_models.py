
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from dataclasses_json import dataclass_json, config
from marshmallow import fields

from models.day_models import Days
from models.user_models import User


@dataclass_json
@dataclass
class CompanyMigrationResult:
    id: int
    counting_date_range: Days
    start_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    end_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    time_consuming: int
    domain_name: str
    name: str
    site_url: str
    scan_file_dir: str


