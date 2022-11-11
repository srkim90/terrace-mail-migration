import json
import os
from datetime import datetime, date
from typing import List, Dict, Union

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from marshmallow import fields

from enums.migration_result_type import UserMigrationResultType, MailMigrationResultType
from models.day_models import Days
from models.user_migration_result_models import UserMigrationResult


@dataclass_json
@dataclass
class CompanyMigrationResult:
    id: int
    counting_date_range: Days
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
    domain_name: str
    name: str
    site_url: str
    n_migration_user_target: int
    n_migration_user_success: int
    n_migration_user_fail: int
    n_migration_mail_target: int
    n_migration_mail_success: int
    n_migration_mail_fail: int
    user_result_type_classify: Dict[str, int]
    mail_result_type_classify: Dict[str, int]
    company_mail_size: int

    # results: List[UserMigrationResult]

    @staticmethod
    def __inc_classify(classify_dict: Dict[str, int], item_name) -> None:
        try:
            classify_dict[item_name] += 1
        except KeyError as e:
            classify_dict[item_name] = 1

    def terminate_company_scan(self):
        self.end_at = datetime.now()
        self.time_consuming = (self.end_at - self.start_at).seconds

    def update_company_scan_result(self, user_report: UserMigrationResult) -> None:
        # self.results.append(user_report)
        self.__inc_classify(self.user_result_type_classify, user_report.result.name)
        if user_report.result == UserMigrationResultType.SUCCESS:
            self.n_migration_user_success += 1
        else:
            self.n_migration_user_fail += 1
        for item in user_report.mail_migration_result_details:
            self.__inc_classify(self.mail_result_type_classify, item.result.name)
            if item.result == MailMigrationResultType.SUCCESS:
                self.n_migration_mail_success += 1
            else:
                self.n_migration_mail_fail += 1


g_start_up_time: str = None


def get_g_start_up_time():
    return get_migration_start_up_time()


def set_g_start_up_time(start_up_time: str):
    global g_start_up_time
    g_start_up_time = start_up_time


def json_serial(obj) -> str:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def get_migration_start_up_time():
    global g_start_up_time
    if g_start_up_time is None:
        g_start_up_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    return g_start_up_time


def save_company_migration_report_as_json(result: CompanyMigrationResult, save_path: str) -> str:
    save_path = os.path.join(save_path, get_migration_start_up_time(), "%d" % result.id)
    if os.path.exists(save_path) is False:
        try:
            os.makedirs(save_path)
        except FileExistsError as e:
            pass
    file_name = os.path.join(save_path, "company_report_%d_%d_%dMB.json" % (
        result.id, result.n_migration_mail_target, result.company_mail_size / (1024 * 1024)))

    #    json_data = CompanyMigrationResult.to_json(result, indent=4, ensure_ascii=False).encode("utf-8")
    #    #json_data = json.dumps(result, indent=4, ensure_ascii=False).encode("utf-8")
    #    with open(file_name, "wb") as fd:
    #        fd.write(json_data)
    dict_data = CompanyMigrationResult.to_dict(result)
    # except UnicodeEncodeError as e:
    #     dict_data = CompanyMigrationResult.to_dict(result).encode("cp949")
    del result
    with open(file_name, "w", encoding='UTF-8') as fd:
        json.dump(dict_data, fd, indent=4, ensure_ascii=False, default=json_serial)
    return file_name
