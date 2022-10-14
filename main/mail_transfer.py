import logging

from common_import import *
from main.cmd.command_line_parser import read_migration_options
from main.cmd.migration_command_option_models import MigrationCommandOptions
from service.mail_migration_service import MailMigrationService
from service.scan_data_provider import ScanDataProvider
from service.signal_service import install_signal
from utils.utills import set_property_path

log = logging.getLogger(__name__)

test_date = "20221012_183946"  # 윈도우에서만 유효!, 실전에선 명령행 파라미터로 받자!


def main() -> None:
    install_signal()
    option: MigrationCommandOptions = read_migration_options(test_date)
    provider: ScanDataProvider = ScanDataProvider()
    set_property_path(option.application_yml_path)
    for company in provider.get_company_report_data(option.target_scan_date, company_ids=option.target_company_ids):
        transfer = MailMigrationService(company)
        transfer.run(user_ids=option.target_user_ids)


if __name__ == '__main__':
    main()
