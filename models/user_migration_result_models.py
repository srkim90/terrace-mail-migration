
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
    name: str
    message_store: str
    time_consuming: int
    n_migration_target: int
    n_migration_success: int
    n_migration_fail: int


