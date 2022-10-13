import argparse
import logging
import sys
from typing import List, Union

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from service.mail_migration_service import MailMigrationService
from service.scan_data_provider import ScanDataProvider
from utils.utills import is_windows

log = logging.getLogger(__name__)

test_date = "20221012_183946"


@dataclass_json
@dataclass
class MigrationCommandOptions:
    target_company_ids: Union[List[int], None]
    target_user_ids: Union[List[int], None]
    target_scan_date: Union[str, None]


def main() -> None:
    option: MigrationCommandOptions = read_options()
    provider: ScanDataProvider = ScanDataProvider()
    for company in provider.get_company_report_data(option.target_scan_date, company_ids=option.target_company_ids):
        transfer = MailMigrationService(company)
        transfer.run(user_ids=option.target_user_ids)


def parser_list(value: str) -> Union[List[int], None]:
    result: List[int] = []
    if type(value) is not str:
        return None
    values = value.strip().split(",")
    for item in values:
        result.append(int(item.strip()))
    return result


def read_options() -> MigrationCommandOptions:
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description="The parsing commands lists.")
    parser.add_argument("-c", "--company-id", help="마이그레이션 대상 회사 ID : 복수개 입력시 쉼표(,) 으로 구분; 입력하지 않을 경우 모든 회사 대상으로 "
                                                   "마이그레이션 수행")
    parser.add_argument("-u", "--user-id", help="마이그레이션 대상 사용자 ID : 복수개 입력시 쉼표(,) 으로 구분; 입력하지 않을 경우 모든 사용자 대상으로 "
                                                "마이그레이션 수행")
    parser.add_argument("-t", "--target-scan-date", help="마이그레이션 수행 대상 데이터 파일 위치 (mail_scanner.py 의 결과 디렉토리)")
    try:
        opts = parser.parse_args(args)
        target_scan_date = opts.target_scan_date
        if target_scan_date is None and is_windows() is True:
            target_scan_date = test_date
        if target_scan_date is None:
            raise FileNotFoundError
        return MigrationCommandOptions(
            target_company_ids=parser_list(opts.company_id),
            target_user_ids=parser_list(opts.user_id),
            target_scan_date=target_scan_date
        )
    except Exception as e:
        print("Error : %s" % e)
        parser.print_help()
        exit()


if __name__ == '__main__':
    main()
