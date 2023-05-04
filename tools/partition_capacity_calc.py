import datetime
import gzip
import json
import multiprocessing
import os
import re
import sys
import threading
from typing import Dict, List, Union

from models.user_models import User

MAX_WORK_PROC = 8
# TIME_SOURCE = "msg_receive"  # DB에 저장된 수신 된 값 기준으로 결과 산출
TIME_SOURCE = "st_ctime"  # 파일 자체의 c_time 기준으로 결과 산출


class PartitionCapacityCalc:
    date_mail_size_classify: Dict[str, int]

    def __init__(self) -> None:
        super().__init__()
        self.lock = threading.Semaphore(1)
        self.date_mail_size_classify = {}

    @staticmethod
    def __is_company_id_dir(dir_name) -> bool:
        pattern = r'^\d+$'
        return bool(re.match(pattern, dir_name))

    @staticmethod
    def __is_user_scan_result(file_name) -> bool:
        # pattern = r"user_\w+\.json"
        # return bool(re.match(pattern, file_name))
        if "user_" not in file_name:
            return False
        if ".json" not in file_name:
            return False
        return True

    @staticmethod
    def __load_user(user_json: bytes) -> User:
        user_dict = json.loads(user_json)
        return user_dict
        # for message in user_dict["messages"]:
        #     message: dict
        #     if "is_webfolder" not in message.keys():
        #         message["is_webfolder"] = ""
        #     if "bytes_full_path" not in message.keys():
        #         message["bytes_full_path"] = ""
        #     if "email_file_coding" not in message.keys():
        #         message["email_file_coding"] = False
        # return User.from_dict(user_dict)

    @staticmethod
    def __report_at(yyyymm: str, data_size: int):
        gb_data_size = data_size / (1024 * 1024 * 1024)
        per_tb_threshold = (1024 * 1024 * 1024 * 1024) / data_size
        print("%s: 해당_월_메일_사이즈=%dByte(%0.2fGB), 1TB_디스크_수용_가능_개월_수=%0.2f month" % (
            yyyymm, data_size, gb_data_size, per_tb_threshold))

    @staticmethod
    def __handle_a_user(user: User, date_mail_size_classify: Dict[str, int]):
        for message in user["messages"]:
            hardlink_count = int(message["hardlink_count"])
            hardlink_count = 1 if hardlink_count <= 0 else hardlink_count
            size = int(message["st_size"] / hardlink_count)
            dt = datetime.datetime.fromtimestamp(message["st_ctime"])
            yyyymm = dt.strftime("%Y-%m")
            try:
                date_mail_size_classify[yyyymm] += size
            except KeyError:
                date_mail_size_classify[yyyymm] = size
        return

    def report(self):
        total_size = 0
        for yyyymm in sorted(list(self.date_mail_size_classify.keys()), reverse=False):
            data_size = self.date_mail_size_classify[yyyymm]
            self.__report_at(yyyymm, data_size)
            total_size += data_size
        print("total_size = %d (%0.2fGB)" % (total_size, total_size / (1024 * 1024 * 1024)))

    @staticmethod
    def calc_multi_process(idx, full_dirs: List[str], result_file_path: str) -> str:
        date_mail_size_classify: Dict[str, int] = {}
        for jdx, full_dir in enumerate(full_dirs):
            if jdx % MAX_WORK_PROC != idx:
                continue
            print("[%d/%d] Start calculate scan result : target_path=%s" % (jdx, len(full_dirs), full_dir))
            for file_name in os.listdir(full_dir):
                if PartitionCapacityCalc.__is_user_scan_result(file_name) is False:
                    continue
                full_file_nane = os.path.join(full_dir, file_name)
                if ".gz" in full_file_nane.lower():
                    fd = gzip.open(full_file_nane, "rb")
                else:
                    fd = open(full_file_nane, "rb")
                json_data = fd.read()
                fd.close()
                PartitionCapacityCalc.__handle_a_user(PartitionCapacityCalc.__load_user(json_data),
                                                      date_mail_size_classify)
        json_data = json.dumps(date_mail_size_classify, indent=4)
        with open(result_file_path, "wb") as fd:
            fd.write(json_data.encode())
        return json_data

    def calc_multi_process_th(self, idx, full_dirs: List[str]) -> Union[None, Dict[str, int]]:
        result_file_path = ".tmp_file_calc_multi_process_th_%d.json" % (idx,)
        proc = multiprocessing.Process(target=PartitionCapacityCalc.calc_multi_process,
                                       args=(idx, full_dirs, result_file_path))
        proc.start()
        proc.join()
        if os.path.exists(result_file_path) is False:
            return None
        with open(result_file_path, "rb") as fd:
            data = fd.read()
            local_classify: Dict[str, int] = json.loads(data)
        os.remove(result_file_path)
        # print(result_dict)
        self.lock.acquire()
        for yyyymm in local_classify.keys():
            size_all = local_classify[yyyymm]
            try:
                self.date_mail_size_classify[yyyymm] += size_all
            except KeyError:
                self.date_mail_size_classify[yyyymm] = size_all
        self.lock.release()
        return local_classify

    def calc(self, data_path: str):
        full_dirs: List[str] = []
        proc_all: List[threading.Thread] = []
        for dir_name in os.listdir(data_path):
            if self.__is_company_id_dir(dir_name) is False:
                continue
            full_dir = os.path.join(data_path, dir_name)
            if os.path.isdir(full_dir) is False:
                continue
            full_dirs.append(full_dir)

        for idx in range(MAX_WORK_PROC):
            h_thread = threading.Thread(target=self.calc_multi_process_th, args=(idx, full_dirs))
            h_thread.daemon = True
            h_thread.start()
            proc_all.append(h_thread)

        for proc in proc_all:
            proc.join()


def print_help(error_message: str):
    print("Invalid input parameter : %s" % (error_message,))
    print("사용법: python partition_capacity_calc.py [scan-report 1] [scan-report 2] [scan-report 3] .....")
    print("ex   : python partition_capacity_calc.py 20221203_203500")
    print("tip  : 서로 다른 장비에서 스캔한 복수개의 결과를 취합 하고 싶다면 파라미터로 각각의 scan-report를 줄줄이 입력하시오 ")
    return


# TEST_PATH = "D:\\data\\20221203_203500"

def check_param() -> List[str]:
    paths = []
    for idx, path in enumerate(sys.argv):
        if idx == 0:
            continue
        if os.path.exists(path) is False or os.path.isdir(path):
            print_help("유효하지 않는 scan-report 경로 '%s'" % (path,))
            exit(-1)
        paths.append(path)
    if len(paths) == 0:
        print_help("입력한 scan-report 경로가 하나도 없습니다")
        exit(-1)
    return paths


def main():
    paths = check_param()
    e = PartitionCapacityCalc()
    for path in paths:
        e.calc(path)
    e.report()


if __name__ == "__main__":
    main()
