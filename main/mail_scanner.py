import logging

from common_import import *
from main.cmd.command_line_parser import read_scan_options
from main.cmd.scan_command_option_models import ScanCommandOptions
from service.signal_service import install_signal

sys.path.append("../binary/Python-minimum/site-packages")

from service.pgsql_scaner_service import PostgresqlSqlScanner

log = logging.getLogger(__name__)


def main() -> None:
    install_signal()
    option: ScanCommandOptions = read_scan_options()
    psql = PostgresqlSqlScanner(option)
    psql.report_user_and_company(option)


if __name__ == '__main__':
    main()
