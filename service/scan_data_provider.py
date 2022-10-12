import os
from typing import List

from models.company_models import Company, load_company_from_json
from service.property_provider_service import ApplicationSettings, ReportSettings, application_container


class ScanDataProvider:
    setting_provider: ApplicationSettings = application_container.setting_provider

    def __init__(self) -> None:
        super().__init__()
        self.property: ReportSettings = self.setting_provider.report

    def get_company_report_data(self, tag: str, company_id: int = -1) -> List[Company]:
        report_path = os.path.join(os.path.join(self.property.report_path, tag, "companies"))
        for file_name in os.listdir(report_path):
            full_path = os.path.join(report_path, file_name)
            if full_path.split(".")[-1].lower() != "json":
                continue
            try:
                __company_id = int(file_name.split("company_report_")[1].split("_")[0])
            except Exception as e:
                continue
            if company_id != -1 and __company_id != company_id:
                continue
            yield load_company_from_json(full_path)
