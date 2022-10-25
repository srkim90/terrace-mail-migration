import logging

from common_import import *
from main.cmd.command_line_parser import read_migration_options
from main.cmd.migration_command_option_models import MigrationCommandOptions
from models.company_global_migration_result_models import CompanyGlobalMigrationResult, \
    save_company_global_migration_report_as_json
from models.company_migration_result_models import CompanyMigrationResult
from service.logging_service import LoggingService
from service.mail_migration_service import MailMigrationService
from service.property_provider_service import application_container, ApplicationSettings
from service.scan_data_provider import ScanDataProvider
from service.signal_service import install_signal, get_stop_flags
from utils.utills import set_property_path

log = logging.getLogger(__name__)

test_date = "20221024_164325"  # 윈도우에서만 유효!, 실전에선 명령행 파라미터로 받자!


def main() -> None:
    install_signal()
    option: MigrationCommandOptions = read_migration_options(test_date)
    provider: ScanDataProvider = ScanDataProvider()
    set_property_path(option.application_yml_path)
    logger: LoggingService = application_container.logger
    setting_provider: ApplicationSettings = application_container.setting_provider
    global_stat: CompanyGlobalMigrationResult = CompanyGlobalMigrationResult()
    for company in provider.get_company_report_data(option.target_scan_data, company_ids=option.target_company_ids):
        if get_stop_flags() is True:
            logger.info("Stop mail migration : stop signal detected!")
            break
        transfer = MailMigrationService(company)
        local_stat: CompanyMigrationResult = transfer.run(user_ids=option.target_user_ids)
        global_stat.update(local_stat)
        save_company_global_migration_report_as_json(global_stat, setting_provider.report.migration_result)
    return


if __name__ == '__main__':
    main()
