import json
import os
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
    start_at: Union[datetime, None]
    commit_start_at: Union[datetime, None]
    commit_end_at: Union[datetime, None]
    end_at: Union[datetime, None]
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

def save_user_migration_report_as_json(result: UserMigrationResult, save_path: str, company_id: int) -> str:
    from models.company_migration_result_models import get_migration_start_up_time, json_serial
    save_path = os.path.join(save_path, get_migration_start_up_time(), "%d" % company_id)
    if os.path.exists(save_path) is False:
        try:
            os.makedirs(save_path)
        except FileExistsError as e:
            pass
    file_name = os.path.join(save_path, "%d.json" % (result.id,))

    dict_data = UserMigrationResult.to_dict(result)
    with open(file_name, "w", encoding='UTF-8') as fd:
        json.dump(dict_data, fd, indent=4, ensure_ascii=False, default=json_serial)
    return file_name
