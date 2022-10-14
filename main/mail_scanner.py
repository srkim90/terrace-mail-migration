import logging

import sys
from common_import import *
from main.cmd.command_line_parser import read_scan_options
from main.cmd.scan_command_option_models import ScanCommandOptions
from service.signal_service import install_signal
from utils.utills import set_property_path

sys.path.append("../binary/Python-minimum/site-packages")

from service.pgsql_scaner_service import PostgresqlSqlScanner

log = logging.getLogger(__name__)


def main() -> None:
    install_signal()
    option: ScanCommandOptions = read_scan_options()
    psql = PostgresqlSqlScanner(option.scan_data_save_dir)
    psql.report_user_and_company(option.scan_range, option.target_company_ids)


if __name__ == '__main__':
    main()
