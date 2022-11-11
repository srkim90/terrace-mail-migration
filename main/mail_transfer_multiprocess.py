import os
import subprocess
import sys
import threading
from datetime import datetime

from common_import import *
import logging
from typing import List

from main.cmd.command_line_parser import read_migration_options
from main.cmd.migration_command_option_models import MigrationCommandOptions
from models.company_global_migration_result_models import CompanyGlobalMigrationResult, load_migration_report, \
    save_company_global_migration_report_as_json
from models.company_migration_result_models import set_g_start_up_time
from service.property_provider_service import application_container, ApplicationSettings

log = logging.getLogger(__name__)

test_date = "20221110_173511"  # 윈도우에서만 유효!, 실전에선 명령행 파라미터로 받자!


class MailMigrationMultiProcessLoader:
    def __init__(self) -> None:
        super().__init__()
        self.h_threads: List[threading.Thread] = []
        self.option: MigrationCommandOptions = read_migration_options(test_date)
        self.setting_provider: ApplicationSettings = application_container.setting_provider
        self.start_up_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        set_g_start_up_time(self.start_up_time)
        self.report: CompanyGlobalMigrationResult = None


    def __get_proc_count(self) -> int:
        if self.setting_provider.system.max_migration_process is None:
            return 1
        return self.setting_provider.system.max_migration_process

    def __make_command(self, rr_index: int) -> str:
        cmd = ""
        python_file = sys.argv[0].replace("mail_transfer_multiprocess.py", "mail_transfer.py")
        args: List[str] = [sys.executable, python_file]
        args.append("--target-scan-data=%s" % self.option.target_scan_data)
        if self.option.target_company_ids is not None:
            args.append("--company-id=%s" % self.option.target_company_ids)
        if self.option.target_user_ids is not None:
            args.append("--user-id=%s" % self.option.target_user_ids)
        if self.option.application_yml_path is not None:
            args.append("--application-yml-path=%s" % self.option.application_yml_path)
        args.append("--round-robin-index=%d" % rr_index)
        args.append("--start-up-time=%s" % self.start_up_time)
        for item in args:
            cmd += "%s " % (item,)
        return cmd

    def __run_thread(self, cmd: str):
        h_thread = threading.Thread(target=self.__wait_thread, args=(cmd,))
        h_thread.daemon = True
        h_thread.start()
        self.h_threads.append(h_thread)

    def __wait_thread(self, cmd):
        subprocess.run(cmd, shell=True)

    def __add_stat(self, report: CompanyGlobalMigrationResult) -> None:
        if self.report is None:
            self.report = report
            return
        if self.report.end_at < report.end_at:
            self.report.end_at = report.end_at
        if self.report.time_consuming < report.time_consuming:
            self.report.time_consuming = report.time_consuming
        self.report.n_migration_user_target += report.n_migration_user_target
        self.report.n_migration_user_success += report.n_migration_user_success
        self.report.n_migration_user_fail += report.n_migration_user_fail
        self.report.n_migration_mail_target += report.n_migration_mail_target
        self.report.n_migration_mail_success += report.n_migration_mail_success
        self.report.n_migration_mail_fail += report.n_migration_mail_fail
        for item in report.user_result_type_classify.keys():
            try:
                self.report.user_result_type_classify[item] += report.user_result_type_classify[item]
            except KeyError:
                self.report.user_result_type_classify[item] = report.user_result_type_classify[item]
        for item in report.mail_result_type_classify.keys():
            try:
                self.report.mail_result_type_classify[item] += report.mail_result_type_classify[item]
            except KeyError:
                self.report.mail_result_type_classify[item] = report.mail_result_type_classify[item]

    def assemble_stat(self):
        result_path = os.path.join(self.setting_provider.report.migration_result, self.start_up_time)
        for item in os.listdir(result_path):
            full_path = os.path.join(result_path, item)
            if os.path.isfile(full_path) is False:
                continue
            if 'migration_statistic_report_' not in item:
                continue
            if ".json" not in item:
                continue
            report: CompanyGlobalMigrationResult = load_migration_report(full_path)
            self.__add_stat(report)
        save_company_global_migration_report_as_json(self.report, self.setting_provider.report.migration_result)


    def run(self):
        for rr_index in range(self.__get_proc_count()):
            self.__run_thread(
                self.__make_command(rr_index)
            )
        for h_thread in self.h_threads:
            h_thread.join()

def main():
    e = MailMigrationMultiProcessLoader()
    e.run()
    e.assemble_stat()


if __name__ == '__main__':
    main()
