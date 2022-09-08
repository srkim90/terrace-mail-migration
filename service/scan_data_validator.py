import os
from typing import List

from models.company_models import Company, load_company_from_json
from models.company_validation_models import CompanyValidationModels
from service.property_provider_service import ApplicationContainer, ApplicationSettings, ReportSettings
from utils.utills import make_data_file_path


class ScanDataValidator:
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()

    def __init__(self) -> None:
        super().__init__()
        self.property: ReportSettings = self.setting_provider.report

    def load_companies(self) -> List[Company]:
        companies: List[Company] = []
        report_path = self.property.report_path
        for item in os.listdir(report_path):
            companies.append(load_company_from_json(os.path.join(report_path, item)))
        return companies

    def report(self):
        companies: List[Company] = self.load_companies()
        for company in companies:
            validator = CompanyValidationModels()
            for user in company.users:
                for mail in user.messages:
                    validator.add_mail(make_data_file_path(mail.full_path))
            report = CompanyValidationModels.to_json(validator, indent=4, ensure_ascii=False)
            print(report)
