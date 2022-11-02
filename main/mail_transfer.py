from common_import import *
import logging
import multiprocessing
from time import sleep
from typing import Union, List

from main.cmd.command_line_parser import read_migration_options
from main.cmd.migration_command_option_models import MigrationCommandOptions
from models.company_global_migration_result_models import CompanyGlobalMigrationResult, \
    save_company_global_migration_report_as_json
from models.company_migration_result_models import CompanyMigrationResult
from models.company_models import load_company_from_json
from service.logging_service import LoggingService
from service.mail_migration_service import MailMigrationService
from service.property_provider_service import application_container, ApplicationSettings
from service.scan_data_provider import ScanDataProvider
from service.signal_service import install_signal, get_stop_flags
from utils.utills import set_property_path

log = logging.getLogger(__name__)

test_date = "20221102_162826"  # 윈도우에서만 유효!, 실전에선 명령행 파라미터로 받자!


class MailMigrationLoader:
    def __init__(self) -> None:
        super().__init__()
        install_signal()
        self.option: MigrationCommandOptions = read_migration_options(test_date)
        self.provider: ScanDataProvider = ScanDataProvider()
        set_property_path(self.option.application_yml_path)
        self.logger: LoggingService = application_container.logger
        self.setting_provider: ApplicationSettings = application_container.setting_provider
        self.global_stat: CompanyGlobalMigrationResult = CompanyGlobalMigrationResult()

    @staticmethod
    def sub_proc_run(idx: int, full_path: str, target_user_ids: Union[List[int], None]) -> Union[
        None, CompanyMigrationResult]:
        install_signal()
        company = load_company_from_json(full_path)
        transfer = MailMigrationService(company)
        local_stat: CompanyMigrationResult = transfer.run(user_ids=target_user_ids)
        return local_stat

    def __update_global_stat(self, result_stat: CompanyMigrationResult):
        self.global_stat.update(result_stat)
        save_company_global_migration_report_as_json(self.global_stat,
                                                     self.setting_provider.report.migration_result)

    def __check_and_wait(self, h_proc_list, is_wait: bool, n_max_thread: int) -> Union[None, CompanyMigrationResult]:
        if is_wait is True:
            if len(h_proc_list) < n_max_thread:
                return None
        while True:
            for idx, h_proc in enumerate(h_proc_list):
                try:
                    data = h_proc.get(timeout=0)
                    del h_proc_list[idx]
                    self.__update_global_stat(data)
                    return data
                except multiprocessing.context.TimeoutError:
                    pass
            sleep(0.1)

    def run_async(self, n_proc):
        h_proc_list = []
        proc_pool = multiprocessing.Pool(processes=n_proc)
        for idx, (company, full_path) in enumerate(self.provider.get_company_report_data(self.option.target_scan_data,
                                                                        company_ids=self.option.target_company_ids)):
            if get_stop_flags() is True:
                self.logger.info("Stop mail migration : stop signal detected!")
                break
            h_proc_list.append(
                proc_pool.apply_async(MailMigrationLoader.sub_proc_run, [idx, full_path, self.option.target_user_ids])
            )
            self.__check_and_wait(h_proc_list, True, n_proc)
        while len(h_proc_list) > 0:
            self.__check_and_wait(h_proc_list, False, n_proc)
        return

    def run(self) -> None:
        for idx, (company, full_path) in enumerate(self.provider.get_company_report_data(self.option.target_scan_data,
                                                                        company_ids=self.option.target_company_ids)):
            if get_stop_flags() is True:
                self.logger.info("Stop mail migration : stop signal detected!")
                break
            local_stat = self.sub_proc_run(idx, full_path, self.option.target_user_ids)
            self.global_stat.update(local_stat)
            save_company_global_migration_report_as_json(self.global_stat,
                                                         self.setting_provider.report.migration_result)
        return


def main():
    e = MailMigrationLoader()
    e.run()


if __name__ == '__main__':
    main()
