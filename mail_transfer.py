import logging

from service.mail_transfer_service import MailTransferService
from service.property_provider_service import ApplicationSettings, ApplicationContainer
from service.scan_data_provider import ScanDataProvider
from service.scan_data_validator import ScanDataValidator

log = logging.getLogger(__name__)


def main() -> None:
    company_file = "D:\\data\\report\\company_report_10_6676_169MB.json"
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()
    provider: ScanDataProvider = ScanDataProvider()
    for company in provider.get_company_report_data('20221006_130253'):
        transfer = MailTransferService(company)
        transfer.run()


if __name__ == '__main__':
    main()
