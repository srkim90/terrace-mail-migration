import argparse
import datetime
import os
import sys
from typing import Union, List

from main.cmd.mail_sender_option_models import SenderCommandOptions
from main.cmd.migration_command_option_models import MigrationCommandOptions
from main.cmd.orphan_command_option_models import OrphanCommandOptions
from main.cmd.scan_command_option_models import ScanCommandOptions
from models.day_models import Days

from utils.utills import is_windows


def validate_application_yml_path(yml_file_name: Union[str, None]) -> None:
    null_list = ["null", "none", "empty", "no", "n", "not"]
    if yml_file_name is None:
        return None
    if yml_file_name.lower() in null_list:
        return None
    if os.path.exists(yml_file_name) is False:
        print("입력한 application.yml 파일이 존재하지 않습니다")
        exit()


def parser_list(value: Union[str, None]) -> Union[List[int], None]:
    null_list = ["null", "none", "empty", "no", "n", "not"]
    if value is None:
        return None
    if value.lower() in null_list:
        return None
    result: List[int] = []
    if type(value) is not str:
        return None
    values = value.strip().split(",")
    for item in values:
        result.append(int(item.strip()))
    return result


def print_help(parser: argparse.ArgumentParser):
    help_str = ["-h", "help", "--help", "-v", "--version", "ver", "-ver", "--ver", "version"]
    args = sys.argv[1:]
    if len(args) == 0:
        return
    if args[0] in help_str:
        parser.print_help()
        exit(0)


def read_date(date_str: str) -> Union[None, datetime.datetime]:
    check_format = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d_%H:%M:%S", "%Y%m%d_%H%M%S", "%Y%m%d %H%M%S", "%Y-%m-%dT%H:%M:%S",
                    "%Y%m%d", "%Y-%m-%d", "%Y.%m.%d"]
    for __format in check_format:
        try:
            return datetime.datetime.strptime(date_str, __format)
        except Exception as e:
            pass
    return None


def read_scan_options() -> ScanCommandOptions:
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description="The parsing commands lists.")
    parser.add_argument("-p", "--application-yml-path",
                        help="(OPTIONAL) application.yml 파일의 경로, 없을 경우 자동으로 찾는다.")
    parser.add_argument("-c", "--company-id",
                        help="(OPTIONAL) 마이그레이션 대상 회사 ID : 복수개 입력시 쉼표(,) 으로 구분; 입력하지 않을 경우 모든 회사 대상으로 "
                             "마이그레이션 수행")
    parser.add_argument("-s", "--start-day",
                        help="(OPTIONAL) 스캔 시작 일자")
    parser.add_argument("-e", "--end-day",
                        help="(OPTIONAL) 스캔 종료 일자")
    parser.add_argument("-d", "--scan-data-save-directory",
                        help="(OPTIONAL) 스캔 결과를 저장하는 디렉토리 지정, 입력하지 않을 경우 자동 생성")
    print_help(parser)
    try:
        scan_range = None
        opts = parser.parse_args(args)
        end_day = opts.end_day
        start_day = opts.start_day
        if end_day is not None:
            scan_range = Days(read_date(start_day), read_date(end_day))

        return ScanCommandOptions(
            application_yml_path=validate_application_yml_path(opts.application_yml_path),
            target_company_ids=parser_list(opts.company_id),
            scan_range=scan_range,
            scan_data_save_dir=opts.scan_data_save_directory
        )
    except Exception as e:
        print("Error : %s" % e)
        parser.print_help()
        exit()


def read_orphan_options() -> OrphanCommandOptions:
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description="The parsing commands lists.")
    parser.add_argument("-p", "--application-yml-path",
                        help="(OPTIONAL) application.yml 파일의 경로, 없을 경우 자동으로 찾는다.")
    try:
        opts = parser.parse_args(args)
        validate_application_yml_path(opts.application_yml_path)
        return OrphanCommandOptions(
            application_yml_path=opts.application_yml_path
        )
    except Exception as e:
        print("Error : %s" % e)
        parser.print_help()
        exit()


def read_sender_options() -> SenderCommandOptions:
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description="The parsing commands lists.")
    parser.add_argument("-c", "--count", help="(OPTIONAL) 보낼 메일 수")
    parser.add_argument("-t", "--mail-to", help="(MANDATORY) 메일 받을 이메일 계정 ex> aaa@srkim.kr,bbb@srkim.kr")
    try:
        opts = parser.parse_args(args)
        count = opts.count
        mail_to = opts.mail_to
        if count is None:
            count = -1
        else:
            count = int(opts.count)
        return SenderCommandOptions(
            n_send_mail=count,
            mail_to=mail_to
        )
    except Exception as e:
        print("Error : %s" % e)
        parser.print_help()
        exit()


def read_migration_options(test_date: str = Union[None, str]) -> MigrationCommandOptions:
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description="The parsing commands lists.")
    parser.add_argument("-d", "--target-scan-date",
                        help="(MANDATORY) 마이그레이션 수행 대상 데이터 파일 위치 (mail_scanner.py 의 결과 디렉토리)")
    parser.add_argument("-c", "--company-id",
                        help="(OPTIONAL) 마이그레이션 대상 회사 ID : 복수개 입력시 쉼표(,) 으로 구분; 입력하지 않을 경우 모든 회사 대상으로 "
                             "마이그레이션 수행")
    parser.add_argument("-u", "--user-id",
                        help="(OPTIONAL) 마이그레이션 대상 사용자 ID : 복수개 입력시 쉼표(,) 으로 구분; 입력하지 않을 경우 모든 사용자 대상으로 "
                             "마이그레이션 수행")
    parser.add_argument("-p", "--application-yml-path",
                        help="(OPTIONAL) application.yml 파일의 경로, 없을 경우 자동으로 찾는다.")
    try:
        opts = parser.parse_args(args)
        target_scan_date = opts.target_scan_date
        if target_scan_date is None and is_windows() is True:
            target_scan_date = test_date
        if target_scan_date is None:
            raise FileNotFoundError("마이그레이션 수행 대상 데이터 파일 위치가 지정 되지 않았습니다. ")
        validate_application_yml_path(opts.application_yml_path)
        return MigrationCommandOptions(
            target_company_ids=parser_list(opts.company_id),
            target_user_ids=parser_list(opts.user_id),
            target_scan_date=target_scan_date,
            application_yml_path=opts.application_yml_path
        )
    except Exception as e:
        print("Error : %s" % e)
        parser.print_help()
        exit()
