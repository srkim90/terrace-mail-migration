from datetime import datetime
from typing import Union

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from marshmallow import fields

from enums.migration_result_type import MailMigrationResultType
from models.mail_models import MailMessage


@dataclass_json
@dataclass
class MailMigrationResult:
    created_at: Union[datetime, None] = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    folder_no: int
    uid_no: int
    result: MailMigrationResultType
    original_full_path: str
    new_full_path: Union[str, None]
    msg_size: int
    msg_receive: int

    @staticmethod
    def builder(mail: MailMessage, result: MailMigrationResultType, new_full_path: str):
        return MailMigrationResult(
            created_at=datetime.now(),
            folder_no=mail.folder_no,
            uid_no=mail.uid_no,
            result=result,
            original_full_path=mail.full_path,
            new_full_path=new_full_path,
            msg_size=mail.msg_size,
            msg_receive=mail.msg_receive
        )