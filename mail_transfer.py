import logging

from service.mail_migration_service import MailMigrationService
from service.property_provider_service import ApplicationSettings, application_container
from service.scan_data_provider import ScanDataProvider

log = logging.getLogger(__name__)

test_date = "20221012_112241"


def test() -> None:
    provider: ScanDataProvider = ScanDataProvider()
    for company in provider.get_company_report_data(test_date, company_id=10):
        transfer = MailMigrationService(company)
        transfer.run(user_id=33)


def main() -> None:
    provider: ScanDataProvider = ScanDataProvider()
    for company in provider.get_company_report_data(test_date):
        transfer = MailMigrationService(company)
        transfer.run()


if __name__ == '__main__':
    main()
