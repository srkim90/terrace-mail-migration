import gzip
import json
import os
import sys

sys.path.append("/opt/terrace-mail-migration")
sys.path.append("/opt/terrace-mail-migration/binary/Python-minimum/site-packages")
from main.orphan_mail_verifier import make_mail_list_file_path
from typing import Dict


class OrphanMailListVerifier:
    f_name_dict: Dict[str, int]
    full_path_dict: Dict[str, int] = {}

    def __init__(self) -> None:
        super().__init__()
        self.f_name_dict = {}
        self.full_path_dict = {}
        orphan_list = os.path.join(make_mail_list_file_path(), "orphan_list.txt")
        with open(orphan_list, "rb") as fd:
            files = fd.read().split(b"\n")
        for line in files:
            line = line.decode()
            f_name = line.split("/")[-1]
            full_path = line
            self.f_name_dict[f_name] = 1
            self.full_path_dict[full_path] = 0

    def check_a_mail(self, full_path: str) -> bool:
        file_name = full_path.split("/")[-1]
        try:
            value = self.f_name_dict[file_name]
            return True
        except KeyError:
            return False

    def run(self):
        path = make_mail_list_file_path()
        all_files = os.listdir(path)
        for idx, f_name in enumerate(all_files):
            if ".json.gz" not in f_name:
                continue
            gz_name = os.path.join(path, f_name)
            print("[%d/%d] gz_name=%s" % (idx, len(all_files), gz_name))
            with gzip.open(gz_name, "rb") as fd:
                company_data = json.loads(fd.read())
                for full_path in company_data["absolute_mail_name_dict"].keys():
                    if self.check_a_mail(full_path) is True:
                        user_mail_db = company_data["absolute_mail_name_dict"][full_path]
                        print("Detect in-use mail: %s -> %s" % (user_mail_db, full_path,))
                    #print("%s" % full_path)


def main():
    e = OrphanMailListVerifier()
    e.run()


if __name__ == '__main__':
    main()
