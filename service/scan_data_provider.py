import os
from typing import List

from models.company_models import Company, load_company_from_json
from models.company_validation_models import CompanyValidationModels
from service.property_provider_service import ApplicationContainer, ApplicationSettings, ReportSettings
from utils.utills import make_data_file_path


class ScanDataProvider:
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()

    def __init__(self) -> None:
        super().__init__()
        self.property: ReportSettings = self.setting_provider.report

    def get_company_report_data(self, tag: str) -> List[Company]:
        report_path = os.path.join(os.path.join(self.property.report_path, tag, "companies"))
        for file_name in os.listdir(report_path):
            full_path = os.path.join(report_path, file_name)
            if full_path.split(".")[-1].lower() != "json":
                continue
            yield load_company_from_json(full_path)
