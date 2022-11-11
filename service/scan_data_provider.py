import os
from typing import List, Union, Tuple

from models.company_models import Company, load_company_from_json
from models.company_scan_statistic_models import get_scan_stat_report_file_name, ScanStatistic, load_scan_stat_from_json
from service.logging_service import LoggingService
from service.property_provider_service import ApplicationSettings, ReportSettings, application_container


class ScanDataProvider:
    setting_provider: ApplicationSettings = application_container.setting_provider
    logger: LoggingService = application_container.logger

    def __init__(self, rr_index: int = -1) -> None:
        super().__init__()
        self.rr_index = rr_index
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


    def __check_company_id_in_check_list(self, file_name: str, company_ids: List[int]) -> bool:
        if company_ids is None:
            return True
        for company_id in company_ids:
            str_id = "%s" % company_id
            if str_id == file_name:
                return True
        return False

    def load_scan_statistic(self, tag: str) -> ScanStatistic:
        stat_path = os.path.join(self.property.report_path, tag, get_scan_stat_report_file_name())
        if os.path.exists(stat_path) is False:
            raise FileNotFoundError("스캔 파일이 완벽하지 않습니다 (not exist : %s)" % (stat_path,))
        return load_scan_stat_from_json(stat_path)

    def __is_skip_by_rr_index(self, index: int) -> bool: # True 일 경우 이 회사는 스킵.
        max_proc = self.setting_provider.system.max_migration_process
        if type(max_proc) is not int:
            return False
        if self.rr_index < 0 or self.rr_index >= max_proc:
            return False
        if index % max_proc == self.rr_index:
            return False
        return True

    def get_company_report_data(self, tag: str, company_ids: Union[List[int], None] = None) -> List[Tuple[Company, str]]:
        jdx = 0
        self.logger.info("target company_ids : %s" % (company_ids,))
        report_path = os.path.join(os.path.join(self.property.report_path, tag))
        for idx, file_name in enumerate(os.listdir(report_path)):
            if self.__check_company_id_in_check_list(file_name, company_ids) is False:
                continue
            full_path = os.path.join(report_path, file_name)
            full_path = self.__get_company_json_name(full_path)
            if full_path is None:
                continue
            jdx += 1
            if self.__is_skip_by_rr_index(jdx) is True:
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
