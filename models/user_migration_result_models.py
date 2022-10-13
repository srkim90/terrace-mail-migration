
from datetime import datetime
from typing import List, Dict, Union

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from marshmallow import fields

from enums.migration_result_type import UserMigrationResultType, MailMigrationResultType
from models.mail_migration_result_models import MailMigrationResult


@dataclass_json
@dataclass
class UserMigrationResult:
    id: int
    start_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    commit_start_at: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    commit_end_at: datetime = field(
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
    time_consuming: Union[float, None]
    time_commit_consuming: Union[float, None]
    n_migration_mail_target: int
    n_migration_mail_success: int
    n_migration_mail_fail: int
    result: UserMigrationResultType
    mail_migration_result_details: List[MailMigrationResult]
    mail_migration_result_type_classify: Dict[str, int]

    @staticmethod
    def __inc_classify(classify_dict: Dict[str, int], item_name) -> None:
        try:
            classify_dict[item_name] += 1
        except KeyError as e:
            classify_dict[item_name] = 1

    def update_mail_migration_result(self, mail_stat: MailMigrationResult):
        if mail_stat.result == MailMigrationResultType.SUCCESS:
            self.n_migration_mail_success += 1
        else:
            self.n_migration_mail_fail += 1
        self.mail_migration_result_details.append(mail_stat)
        self.__inc_classify(self.mail_migration_result_type_classify, mail_stat.result.name)

    def terminate_user_scan(self):
        self.time_commit_consuming = float((self.commit_end_at - self.commit_start_at).microseconds / (1000.0*1000.0))
        self.end_at = datetime.now()
        self.time_consuming = float((self.end_at - self.start_at).microseconds / (1000.0*1000.0))
