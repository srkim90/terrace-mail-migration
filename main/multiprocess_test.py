import datetime
import multiprocessing
import random
from time import sleep
from typing import Union, List

from models.company_migration_result_models import CompanyMigrationResult
from models.day_models import Days


class MultiprocessTest:
    def __init__(self) -> None:
        self.N_MAX_THREAD = 4
        self.proc_pool = multiprocessing.Pool(processes=self.N_MAX_THREAD)
        super().__init__()

    @staticmethod
    def sub_proc_run(idx, full_path: str, target_user_ids: Union[List[int], None]) -> CompanyMigrationResult:
        counting_date_range: None
        # print("idx=%s, full_path=%s, target_user_ids=%s" % (idx, full_path, target_user_ids))
        local_stat: CompanyMigrationResult = CompanyMigrationResult(
            id=idx,
            counting_date_range=Days(datetime.datetime.now(), datetime.datetime.now()),
            start_at=datetime.datetime.now(),
            end_at=None,
            time_consuming=None,
            domain_name="test1",
            name="test2",
            site_url="test3",
            n_migration_user_target=11,
            n_migration_user_success=0,
            n_migration_user_fail=0,
            n_migration_mail_target=1,
            n_migration_mail_success=0,
            n_migration_mail_fail=0,
            user_result_type_classify={},
            mail_result_type_classify={},
            company_mail_size=1212,
            results=[]
        )
        sleep(0.37 * random.randrange(1, 7))
        return local_stat

    def __check_and_wait(self, h_proc_list, is_wait: bool) -> Union[None, CompanyMigrationResult]:
        if is_wait is True:
            if len(h_proc_list) < self.N_MAX_THREAD:
                return None
        while True:
            for idx, h_proc in enumerate(h_proc_list):
                try:
                    data = h_proc.get(timeout=0)
                    del h_proc_list[idx]
                    return data
                except multiprocessing.context.TimeoutError:
                    pass
            sleep(0.1)

    def run(self) -> None:
        h_procs = []


        for idx in range(20):
            h_procs.append(self.proc_pool.apply_async(MultiprocessTest.sub_proc_run, [idx, "1111", [1, 2, 3, 4, 5, ]]))
            result_stat = self.__check_and_wait(h_procs, True)
            if result_stat is None:
                continue
            print(result_stat.id)

        while len(h_procs) > 0:
            result_stat = self.__check_and_wait(h_procs, False)
            print(result_stat.id)
        return


def main():
    e = MultiprocessTest()
    e.run()


if __name__ == "__main__":
    main()
