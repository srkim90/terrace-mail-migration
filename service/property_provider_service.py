import datetime

from pydantic import BaseSettings
from dependency_injector import containers, providers

from models.day_models import Days
from service.logging_service import LoggingService
from service.mail_file_checker_service import MailMessageFileChecker
from utils.utills import get_property


class DatabaseSettings:
    property = get_property()["database"]["postgresql"]
    host: str = property["host"]
    port: int = int(property["port"])
    username: str = property["username"]
    password: str = property["password"]
    database: str = property["database"]


class MailMoveSettings:
    property = get_property()["mail"]["path"]
    origin_mdata_path: str = property["origin-mdata-path"]
    new_mdata_path: str = property["new-mdata-path"]

class DateRangeSettings:
    property = get_property()["date-range"]
    start_day: datetime.datetime = property["start-day"]
    end_day: datetime.datetime = property["end-day"]

    if type(start_day) == datetime.date:
        start_day = datetime.datetime.combine(start_day, datetime.datetime.min.time())

    if type(end_day) == datetime.date:
        end_day = datetime.datetime.combine(end_day, datetime.datetime.min.time())

    date_range: Days = Days(start_day=start_day, end_day=end_day)


class ReportSettings(BaseSettings):
    property = get_property()["report"]
    report_path: str = property["report-path"]
    if "local-test-data-path" in property.keys():
        local_test_data_path: str = property["local-test-data-path"]
    else:
        local_test_data_path = ""


class ApplicationSettings(BaseSettings):
    date_range: DateRangeSettings = DateRangeSettings()
    db: DatabaseSettings = DatabaseSettings()
    report: ReportSettings = ReportSettings()
    move_setting: MailMoveSettings = MailMoveSettings()



class ApplicationContainer(containers.DeclarativeContainer):
    setting_provider = providers.Singleton(ApplicationSettings)
    mail_file_checker = providers.Singleton(MailMessageFileChecker)
    logger: LoggingService = providers.Singleton(LoggingService)
