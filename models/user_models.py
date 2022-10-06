from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from dataclasses_json import dataclass_json, config
from marshmallow import fields

from models.mail_models import MailMessage


@dataclass_json
@dataclass
class User:
    id: int
    mail_user_seq: int
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
    login_id: str
    mail_group: str
    name: str
    message_store: str
    mail_uid: str
    user_mail_count: int
    user_all_mail_count: int
    user_all_mail_size: int
    user_mail_size: int
    user_mail_size_in_db: int
    source_path_not_match_mails: int
    messages: List[MailMessage]
