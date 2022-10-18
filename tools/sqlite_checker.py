import json
import os
import platform
import sqlite3
from typing import List


class SqliteChecker:
    def __init__(self, base_dir: str) -> None:
        super().__init__()
        self.base_dir: str = base_dir

    @staticmethod
    def __db_conn(db_path: str, readonly: bool = True):
        if os.path.exists(db_path) is False:
            raise FileNotFoundError
        try:
            if readonly is True:
                conn = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True)
            else:
                conn = sqlite3.connect('file:%s' % db_path, uri=True)
        except sqlite3.NotSupportedError as e:
            conn = sqlite3.connect('%s' % db_path)
        return conn

    def __list_up_all_mcache_db(self) -> List[str]:
        for subdir_1 in os.listdir(self.base_dir):
            now_dir_1 = os.path.join(self.base_dir, subdir_1)
            for subdir_2 in os.listdir(now_dir_1):
                now_dir_2 = os.path.join(now_dir_1, subdir_2)
                for subdir_3 in os.listdir(now_dir_2):
                    now_dir_3 = os.path.join(now_dir_2, subdir_3)
                    mcache_path = os.path.join(now_dir_3, "_mcache.db")
                    if os.path.exists(mcache_path) is False:
                        continue
                    yield mcache_path

    def list_up_all_mail(self):
        listup = {}
        with open("list_up_all_mail.txt", "w") as fd:
            for mcache_path in self.__list_up_all_mcache_db():
                mcache = self.__db_conn(mcache_path)
                query = "select full_path from mail_message"
                cur = mcache.cursor()
                cur.execute(query)
                for row in cur:
                    full_path = row[0]
                    try:
                        listup[full_path] += 1
                    except KeyError:
                        listup[full_path] = 1
                    fd.write("%s\n" % full_path)
                cur.close()
                mcache.close()
        listup_json = json.dumps(listup, indent=4)
        with open("list_up_all_mail.json", "w") as fd:
            fd.write(listup_json)

def main():
    base_dir = "/data/mdata"
    if "window" in platform.system().lower():
        base_dir = "D:\\data\\cs_mail1\\mindex\\mindex"
    e = SqliteChecker(base_dir)
    e.list_up_all_mail()


if __name__ == "__main__":
    main()
