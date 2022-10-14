import logging

import sys
from common_import import *
from main.cmd.command_line_parser import read_scan_options
from main.cmd.scan_command_option_models import ScanCommandOptions
from utils.utills import set_property_path

sys.path.append("../binary/Python-minimum/site-packages")

from service.pgsql_scaner_service import PostgresqlSqlScanner

log = logging.getLogger(__name__)


def main() -> None:
    option: ScanCommandOptions = read_scan_options()
    set_property_path(option.application_yml_path)
    psql = PostgresqlSqlScanner()
    psql.report_user_and_company(option.scan_range, option.target_company_ids)


if __name__ == '__main__':
    main()
