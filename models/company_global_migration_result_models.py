import json
import os
from datetime import datetime
from typing import List, Dict, Union

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from marshmallow import fields

from enums.migration_result_type import UserMigrationResultType, MailMigrationResultType
from models.company_migration_result_models import CompanyMigrationResult, get_g_start_up_time
from models.day_models import Days
from models.user_migration_result_models import UserMigrationResult


@dataclass_json
@dataclass
class CompanyGlobalMigrationResult:
    # def __init__(self) -> None:
    #     super().__init__()
    #     self.start_at = datetime.now()
    #     self.end_at = None
    #     self.time_consuming = None
    #     self.n_migration_user_target = 0
    #     self.n_migration_user_success = 0
    #     self.n_migration_user_fail = 0
    #     self.n_migration_mail_target = 0
    #     self.n_migration_mail_success = 0
    #     self.n_migration_mail_fail = 0
    #     self.user_result_type_classify = {}
    #     self.mail_result_type_classify = {}
    #     self.company_mail_size = 0
    #     self.counting_date_range = None


    start_at: Union[datetime, None] = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    end_at: Union[datetime, None] = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    time_consuming: Union[int, None]
    n_migration_user_target: int
    n_migration_user_success: int
    n_migration_user_fail: int
    n_migration_mail_target: int
    n_migration_mail_success: int
    n_migration_mail_fail: int
    user_result_type_classify: Dict[str, int]
    mail_result_type_classify: Dict[str, int]
    company_mail_size: int
    counting_date_range: Days

    def update(self, model: CompanyMigrationResult):
        self.end_at = datetime.now()
        self.time_consuming = (self.end_at - self.start_at).seconds
        self.n_migration_user_target += model.n_migration_user_target
        self.n_migration_user_success += model.n_migration_user_success
        self.n_migration_user_fail += model.n_migration_user_fail
        self.n_migration_mail_target += model.n_migration_mail_target
        self.n_migration_mail_success += model.n_migration_mail_success
        self.n_migration_mail_fail += model.n_migration_mail_fail
        self.company_mail_size += model.company_mail_size
        self.counting_date_range = model.counting_date_range
        for key in model.user_result_type_classify.keys():
            value = model.user_result_type_classify[key]
            try:
                self.user_result_type_classify[key] += value
            except KeyError:
                self.user_result_type_classify[key] = value
        for key in model.mail_result_type_classify.keys():
            value = model.mail_result_type_classify[key]
            try:
                self.mail_result_type_classify[key] += value
            except KeyError:
                self.mail_result_type_classify[key] = value
        return


def load_migration_report(full_path) -> CompanyGlobalMigrationResult:
    with open(full_path, "rb") as fd:
        return CompanyGlobalMigrationResult.from_json(fd.read())


def save_company_global_migration_report_as_json(result: CompanyGlobalMigrationResult, save_path: str,
                                                 rr_index=-1) -> str:
    save_path = os.path.join(save_path, get_g_start_up_time())
    if os.path.exists(save_path) is False:
        try:
            os.makedirs(save_path)
        except FileExistsError as e:
            pass
    result.end_at = datetime.now()
    if type(rr_index) == int and rr_index >= 0:
        file_name = os.path.join(save_path, "migration_statistic_report_%d.json" % rr_index)
    else:
        file_name = os.path.join(save_path, "migration_statistic_report.json")

    json_data = CompanyGlobalMigrationResult.to_json(result, indent=4, ensure_ascii=False).encode("utf-8")
    # json_data = json.dumps(result, indent=4, ensure_ascii=False).encode("utf-8")
    with open(file_name, "wb") as fd:
        fd.write(json_data)
    return file_name
