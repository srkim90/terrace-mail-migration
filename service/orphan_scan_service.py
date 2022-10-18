import os
from typing import List

from models.orphan_scan_models import OrphanScanModels
from service.pgsql_scaner_service import PostgresqlSqlScanner
from service.property_provider_service import application_container, ApplicationSettings
from service.sqlite_connector_service import SqliteConnector


class OrphanScanService:
    pg_scanner: PostgresqlSqlScanner = PostgresqlSqlScanner()
    setting_provider: ApplicationSettings = application_container.setting_provider

    def __init__(self) -> None:
        super().__init__()

    def __list_up_mcache_db(self) -> List[str]:
        # \mindex\10\0\1021
        results: List[str] = []
        base_mindex = self.setting_provider.move_setting.mindex_path
        if os.path.exists(base_mindex) is False:
            raise FileNotFoundError("Not exist mindex_path : %s" % base_mindex)
        for lv1 in os.listdir(base_mindex):
            midx_lv1 = os.path.join(base_mindex, lv1)
            if os.path.isdir(midx_lv1) is False:
                continue
            for lv2 in os.listdir(midx_lv1):
                midx_lv2 = os.path.join(midx_lv1, lv2)
                if os.path.isdir(midx_lv2) is False:
                    continue
                for lv3 in os.listdir(midx_lv2):
                    midx_lv3 = os.path.join(midx_lv2, lv3)
                    if os.path.isdir(midx_lv3) is False:
                        continue
                    full_midx_dir = os.path.join(midx_lv3, "_mcache.db")
                    results.append(full_midx_dir)
        return results

    def __str_index_xyx(self, mcache_db_path: str, s_idx=-2):
        mcache_db_path_new = mcache_db_path.replace("\\", "/")
        s_item = mcache_db_path_new.split("/")[s_idx]
        if len(s_item) == 8:
            s_idx -= 1
        mindex_x = mcache_db_path_new.split("/")[s_idx - 2]
        mindex_y = mcache_db_path_new.split("/")[s_idx - 1]
        mindex_z = mcache_db_path_new.split("/")[s_idx - 0]
        return "%s_%s_%s" % (mindex_x, mindex_y, mindex_z)

    def __sort_mindex_list(self, db_list_all: List[str]):
        result_dict = {}
        for mcache_db_path in db_list_all:
            index_xyx = self.__str_index_xyx(mcache_db_path)
            result_dict[index_xyx] = mcache_db_path
        return result_dict

    def __check_orhan_mail_counts(self, mindex: dict, mindex_xyz: str, mail_list: List[str]) -> int:
        n_cnt = 0
        try:
            mindex_db = mindex[mindex_xyz]
        except KeyError:
            return len(mail_list)
        db = SqliteConnector(mindex_db, -1, -1, "")
        db_all_mails = db.get_mail_all_by_hash(only_name=True)
        for mail in mail_list:
            mail_name = mail.replace("\\", "/").split("/")[-1]
            try:
                val = db_all_mails[mail_name]
            except KeyError:
                n_cnt += 1
            #if db.check_mail_exist(mail_name) is False:
            #    n_cnt += 1
        return n_cnt

    def __get_mail_count(self, db_list_all: List[str], db_list_orphan: List[str]) -> (int, int, int):
        all_midxs = self.__sort_mindex_list(db_list_all)
        orphan_midxs = self.__sort_mindex_list(db_list_orphan)

        mail_count = 0
        orphan_mail_count = 0
        orphan2_mail_count = 0
        for mdata_path in self.setting_provider.move_setting.origin_mdata_path:
            for lv1 in os.listdir(mdata_path):
                mdata_lv1 = os.path.join(mdata_path, lv1)
                if os.path.isdir(mdata_lv1) is False:
                    continue
                for lv2 in os.listdir(mdata_lv1):
                    mdata_lv2 = os.path.join(mdata_lv1, lv2)
                    if os.path.isdir(mdata_lv2) is False:
                        continue
                    for lv3 in os.listdir(mdata_lv2):
                        mdata_lv3 = os.path.join(mdata_lv2, lv3)
                        if os.path.isdir(mdata_lv3) is False:
                            continue
                        index_xyx = self.__str_index_xyx(mdata_lv3, s_idx=-1)
                        mail_list: List[str] = []
                        for lv4 in os.listdir(mdata_lv3):
                            mdata_lv4 = os.path.join(mdata_lv3, lv4)
                            if os.path.isdir(mdata_lv4) is False:
                                continue
                            for eml_file in os.listdir(mdata_lv4):
                                full_eml_path = os.path.join(mdata_lv4, eml_file)
                                if os.path.isdir(full_eml_path) is True or ".eml" not in full_eml_path:
                                    continue
                                mail_list.append(full_eml_path)
                        mail_count += len(mail_list)
                        orphan_mail_count += self.__check_orhan_mail_counts(all_midxs, index_xyx, mail_list)
                        orphan2_mail_count += self.__check_orhan_mail_counts(orphan_midxs, index_xyx, mail_list)
        return mail_count, orphan_mail_count, orphan2_mail_count


    def detect(self) -> OrphanScanModels:
        company_count = self.pg_scanner.get_companies_count()
        user_count = self.pg_scanner.get_users_count(all_count=True)
        orphan_user_count = user_count - self.pg_scanner.get_users_count(all_count=False)

        mail_user_count = len(self.pg_scanner.get_mail_user_id_list())
        orphan_mail_users = self.pg_scanner.get_mail_user_id_list(exclude_orphan=True)
        orphan2_mail_users = self.pg_scanner.get_mail_user_id_list(exclude_orphan2=True)
        orphan_mail_user_count = mail_user_count - len(orphan_mail_users)
        orphan2_mail_user_count = mail_user_count - len(orphan2_mail_users)

        mcache_db = self.__list_up_mcache_db()
        orphan_mcache_db = self.pg_scanner.get_valid_mcache_db_count(mcache_db)
        orphan2_mcache_db = self.pg_scanner.get_valid_mcache_db_count(mcache_db, orphan2_mail_users)

        mcache_db_count = len(mcache_db)
        orphan_mcache_db_count = mcache_db_count - len(orphan_mcache_db)
        orphan2_mcache_db_count = mcache_db_count - len(orphan2_mcache_db)

        mail_count, orphan_mail_count, orphan2_mail_count = self.__get_mail_count(mcache_db, orphan2_mcache_db)

        return OrphanScanModels(
            company_count=company_count,

            user_count=user_count,
            orphan_user_count=orphan_user_count,

            mail_user_count=mail_user_count,
            orphan_mail_user_count=orphan_mail_user_count,
            orphan2_mail_user_count=orphan2_mail_user_count,

            mcache_db_count=mcache_db_count,
            orphan_mcache_db_count=orphan_mcache_db_count,
            orphan2_mcache_db_count=orphan2_mcache_db_count,

            mail_count=mail_count,
            orphan_mail_count=orphan_mail_count,
            orphan2_mail_count=orphan2_mail_count
        )


def main():
    e = OrphanScanService()
    scan: OrphanScanModels = e.detect()
    scan.save_as_json()
    return


