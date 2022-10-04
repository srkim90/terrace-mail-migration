import logging

import sys

sys.path.append("./binary/Python-3.6.15-minimum/local/lib/python3.6/site-packages")

from service.pgsql_scaner_service import PostgresqlSqlScanner
from service.property_provider_service import ApplicationSettings, ApplicationContainer

log = logging.getLogger(__name__)


def main() -> None:
    company_id = -1
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()
    psql = PostgresqlSqlScanner()
    psql.report_user_and_company(setting_provider.date_range.date_range, company_id)


if __name__ == '__main__':
    main()
