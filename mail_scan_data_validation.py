import logging

from service.property_provider_service import ApplicationSettings, ApplicationContainer
from service.scan_data_validator import ScanDataValidator

log = logging.getLogger(__name__)


def main() -> None:
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()
    validator: ScanDataValidator = ScanDataValidator()
    validator.report()


if __name__ == '__main__':
    main()
