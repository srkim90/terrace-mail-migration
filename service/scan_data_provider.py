import os
from typing import List, Union, Tuple

from models.company_models import Company, load_company_from_json
from service.logging_service import LoggingService
from service.property_provider_service import ApplicationSettings, ReportSettings, application_container


class ScanDataProvider:
    setting_provider: ApplicationSettings = application_container.setting_provider
    logger: LoggingService = application_container.logger

    def __init__(self) -> None:
        super().__init__()
        self.property: ReportSettings = self.setting_provider.report

    def __get_company_json_name(self, full_path: str) -> Union[str, None]:
        if os.path.isdir(full_path) is False:
            return None
        for file_name in os.listdir(full_path):
            if file_name.split(".")[-1].lower() != "json":
                continue
            if 'company_report' not in file_name:
                continue
            # try:
            #     __company_id = int(file_name.split("company_report_")[1].split("_")[0])
            # except Exception as e:
            #     continue  # report 파일 이름이 유효하지 않다.
            return os.path.join(full_path, file_name)
        return None


    def get_company_report_data(self, tag: str, company_ids: Union[List[int], None] = None) -> List[Tuple[Company, str]]:
        self.logger.info("target company_ids : %s" % (company_ids,))
        report_path = os.path.join(os.path.join(self.property.report_path, tag))
        for file_name in os.listdir(report_path):
            if company_ids is not None and file_name not in company_ids:
                continue
            full_path = os.path.join(report_path, file_name)
            full_path = self.__get_company_json_name(full_path)
            if full_path is None:
                continue
            try:
                company = load_company_from_json(full_path)
            except Exception as e:
                self.logger.error("fail to load company_report skip to migration this company : %s" % (full_path,))
                continue
            if len(company.users) == 0 or company.company_mail_count == 0:
                self.logger.debug("empty user of company skip : full_path=%s, name=%s" % (full_path, company.name))
                continue
            yield company, full_path
