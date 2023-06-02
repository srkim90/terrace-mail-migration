import logging
import os
import subprocess

import sys
import threading
from datetime import datetime
from typing import List

from common_import import *
from main.cmd.command_line_parser import read_scan_options, list_to_command
from main.cmd.scan_command_option_models import ScanCommandOptions
from models.company_migration_result_models import set_g_start_up_time
from models.company_scan_statistic_models import ScanStatistic, get_scan_stat_report_file_name, \
    load_scan_stat_from_json, save_scan_stat_as_json, merge_scan_stat
from service.logging_service import LoggingService
from service.property_provider_service import ApplicationSettings, application_container
from service.signal_service import install_signal

sys.path.append("../binary/Python-minimum/site-packages")

from service.pgsql_scaner_service import PostgresqlSqlScanner

log = logging.getLogger(__name__)



class MailScanMultiProcessLoader:
    logger: LoggingService = application_container.logger

    def __init__(self) -> None:
        super().__init__()
        self.h_threads: List[threading.Thread] = []
        self.option: ScanCommandOptions = read_scan_options()
        self.setting_provider: ApplicationSettings = application_container.setting_provider
        self.start_up_time = datetime.now().strftime("%Y%m%d_%H%M%S")  # 스켄 결과 저장 경로로 쓴다.
        self.report: ScanStatistic = None
        self.logger.info("%s" % self.option)

    def __get_proc_count(self) -> int:
        if self.setting_provider.system.max_work_process is None:
            return 1
        return self.setting_provider.system.max_work_process

    def __make_command(self, rr_index: int) -> str:
        cmd = ""
        python_file = sys.argv[0].replace("mail_scanner_multiprocess.py", "mail_scanner.py")
        args: List[str] = [sys.executable, python_file]
        if self.option.target_company_ids is not None:
            args.append("--company-id=%s" % list_to_command(self.option.target_company_ids))
        if self.option.exclude_company_ids is not None:
            args.append("--exclude-company-id=%s" % list_to_command(self.option.exclude_company_ids))
        if self.option.scan_range is not None:
            if self.option.scan_range.start_day is not None:
                args.append("--start-day=%s" % self.option.scan_range.start_day.strftime("%Y-%m-%d"))
            if self.option.scan_range.end_day is not None:
                args.append("--end-day=%s" % self.option.scan_range.end_day.strftime("%Y-%m-%d"))
        if self.option.application_yml_path is not None:
            args.append("--application-yml-path=%s" % self.option.application_yml_path)
        if self.option.scan_data_save_dir is not None:
            args.append("--scan-data-save-directory=%s" % self.option.scan_data_save_dir)
            self.start_up_time = self.option.scan_data_save_dir
        else:
            args.append("--scan-data-save-directory=%s" % self.start_up_time)
        args.append("--round-robin-index=%d" % rr_index)
        for item in args:
            cmd += "%s " % (item,)
        return cmd

    def __run_thread(self, cmd: str):
        h_thread = threading.Thread(target=self.__wait_thread, args=(cmd,))
        h_thread.daemon = True
        h_thread.start()
        self.h_threads.append(h_thread)

    def __wait_thread(self, cmd):
        self.logger.info("run subprocess : %s" % (cmd,))
        subprocess.run(cmd, shell=True)

    def __add_stat(self, report: ScanStatistic) -> None:
        if self.report is None:
            self.report = report
            return
        self.report = merge_scan_stat(self.report, report)
        return

    def assemble_stat(self):
        self.logger.info("---=== start merge subprocess stat ===---")
        report_file_name = get_scan_stat_report_file_name() # scan_statistic_report.json
        prefix = report_file_name.replace(".json", "_")
        result_path = os.path.join(self.setting_provider.report.report_path, self.start_up_time)
        self.logger.info("result_path : %s" % result_path)
        for item in os.listdir(result_path):
            full_path = os.path.join(result_path, item)
            if os.path.isfile(full_path) is False:
                continue
            self.logger.info("file : %s" % full_path)
            if prefix not in item:
                continue
            if ".json" not in item:
                continue
            report: ScanStatistic = load_scan_stat_from_json(full_path)
            self.__add_stat(report)
        save_scan_stat_as_json(self.report, result_path)
        self.logger.companies_scan_complete_logging(self.report)


    def run(self):
        for rr_index in range(self.__get_proc_count()):
            self.__run_thread(
                self.__make_command(rr_index)
            )
        for h_thread in self.h_threads:
            h_thread.join()

def main() -> None:
    loader = MailScanMultiProcessLoader()
    loader.run()
    loader.assemble_stat()


if __name__ == '__main__':
    main()
