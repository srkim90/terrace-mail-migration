import datetime
import os
import re
from typing import List, Union, Tuple

try:
    from pydantic import BaseSettings
except Exception:
    from pydantic_settings import BaseSettings
from dependency_injector import containers, providers

from enums.move_strategy_type import MoveStrategyType, move_strategy_type_converter
from models.day_models import Days
from service.logging_service import LoggingService
from service.mail_file_checker_service import MailMessageFileChecker
from service.mail_migration_logging_service import MailMigrationLoggingService
from utils.utills import get_property, parser_dir_list


class DatabaseSettings:
    property = get_property()["database"]["postgresql"]
    host: str = property["host"]
    port: int = int(property["port"])
    username: str = property["username"]
    password: str = property["password"]
    database: str = property["database"]


class SystemSettings:
    max_work_threads: int = get_property()["system"]["max-work-threads"]
    max_work_process: int = get_property()["system"]["max-work-process"]
    max_migration_threads: int = get_property()["system"]["max-migration-threads"]
    max_migration_process: int = get_property()["system"]["max-migration-process"]


def handle_threshold_ratio(property_value: str) -> Union[int, List[Tuple[str, int, str]]]:
    try:
        return int(property_value)
    except ValueError as e:
        pass
    volume_dict = {}
    result_list: List[Tuple[str, int, str]] = []
    for line in property_value.split(","):
        if ":" not in line:
            continue

        volume = line.split(":")[0].strip()
        value = line.split(":")[1].strip().lower()
        numbers = int(re.sub(r'[^0-9]', '', value))
        unit = "%"
        if 'byte' in value or 'b' in value:
            numbers = numbers * 1
            unit = "byte"
        elif 'kb' in value:
            numbers = numbers * 1024
            unit = "byte"
        elif 'mb' in value:
            numbers = numbers * 1024 * 1024
            unit = "byte"
        elif 'gb' in value:
            numbers = numbers * 1024 * 1024 * 1024
            unit = "byte"
        elif 'tb' in value:
            numbers = numbers * 1024 * 1024 * 1024 * 1024
            unit = "byte"
        #print("volume=%s, value=%s, unit=%s" % (volume, numbers, unit))
        volume_dict[volume] = (volume, numbers, unit)
    vol_list = list(volume_dict.keys())
    vol_list.sort(key=len, reverse=True)
    for volume in vol_list:
        result_list.append(volume_dict[volume])
    return result_list


class MailMoveSettings:
    property = get_property()["mail"]
    mindex_path: str = property["path"]["mindex-path"]
    origin_mdata_path: List[str] = parser_dir_list(property["path"]["origin-mdata-path"])
    new_mdata_path: List[str] = parser_dir_list(property["path"]["new-mdata-path"])
    partition_capacity_threshold_ratio: Union[int, List[Tuple[str, int, str]]] = handle_threshold_ratio(property["partition-capacity-threshold-ratio"]) #
    move_strategy: MoveStrategyType = move_strategy_type_converter(property["move-strategy"])
    enable_hardlink: str = bool(property["enable-hardlink"])
    final_check_method: str = "size"
    if "final-check-method" in property.keys():
        final_check_method: str = property["final-check-method"]






class DateRangeSettings:
    try:
        property = get_property()["date-range"]
    except KeyError:
        property = {
            "start-day": None,
            "end-day": None
        }
    try:
        start_day: Union[datetime.datetime, None] = property["start-day"]
    except TypeError as e:
        start_day = datetime.datetime.strptime("1975-01-01 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    try:
        end_day: Union[datetime.datetime, None] = property["end-day"]
    except TypeError as e:
        end_day = datetime.datetime.now()

    if type(start_day) == datetime.date:
        start_day = datetime.datetime.combine(start_day, datetime.datetime.min.time())

    if type(end_day) == datetime.date:
        end_day = datetime.datetime.combine(end_day, datetime.datetime.min.time())

    date_range: Days = Days(start_day=start_day, end_day=end_day)


class ReportSettings(BaseSettings):
    property = get_property()["report"]
    report_path: str = property["report-path"]
    migration_result: str = property["migration-result"]
    if "local-test-data-path" in property.keys():
        local_test_data_path: str = property["local-test-data-path"]
    else:
        local_test_data_path = ""


class ApplicationSettings(BaseSettings):
    date_range: DateRangeSettings = DateRangeSettings()
    db: DatabaseSettings = DatabaseSettings()
    report: ReportSettings = ReportSettings()
    move_setting: MailMoveSettings = MailMoveSettings()
    system: SystemSettings = SystemSettings()


class ApplicationContainer: # containers.DeclarativeContainer
    setting_provider = ApplicationSettings() #providers.Singleton(ApplicationSettings)
    mail_file_checker = MailMessageFileChecker() #providers.Singleton(MailMessageFileChecker)
    logger: LoggingService = LoggingService() #providers.Singleton(LoggingService)
    migration_logging = MailMigrationLoggingService() #MailMigrationLoggingService = providers.Singleton(MailMigrationLoggingService)


application_container: ApplicationContainer = ApplicationContainer()
