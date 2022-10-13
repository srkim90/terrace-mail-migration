import argparse
import sys
from typing import Union, List

from main.cmd.migration_command_option_models import MigrationCommandOptions
from main.cmd.scan_command_option_models import ScanCommandOptions

from utils.utills import is_windows


def parser_list(value: str) -> Union[List[int], None]:
    result: List[int] = []
    if type(value) is not str:
        return None
    values = value.strip().split(",")
    for item in values:
        result.append(int(item.strip()))
    return result


def read_scan_options() -> ScanCommandOptions:
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description="The parsing commands lists.")
    parser.add_argument("-p", "--application-yml-path",
                        help="(OPTIONAL) application.yml 파일의 경로, 없을 경우 자동으로 찾는다.")
    parser.add_argument("-c", "--company-id",
                        help="(OPTIONAL) 마이그레이션 대상 회사 ID : 복수개 입력시 쉼표(,) 으로 구분; 입력하지 않을 경우 모든 회사 대상으로 "
                             "마이그레이션 수행")
    try:
        opts = parser.parse_args(args)
        return ScanCommandOptions(
            application_yml_path=opts.application_yml_path,
            target_company_ids=parser_list(opts.company_id)
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
