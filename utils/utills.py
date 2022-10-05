import dataclasses, json
import datetime
import os
import platform
from typing import List

import yaml as yaml


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def mail_scanner_print_usage():
    with open("./README.txt", encoding="utf-8") as fd:
        info = fd.read()
    print(info)


def is_windows() -> bool:
    return "window" in platform.system().lower()


def parser_dir_list(paths: str) -> List[str]:
    parsed_path = []
    for path in paths.split(","):
        path = path.strip()
        if os.path.exists(path) is False:
            print("Error. Not exist dir, check your application.yml : %s" % (path,))
            exit()
        parsed_path.append(path)
    return parsed_path


def get_property() -> dict:
    profile_path = "profile"
    profile_name = "application.yml"
    if is_windows() is True:
        profile_name = "application-develop.yml"
    common_config_file = os.path.join(profile_path, profile_name)
    common_config: dict = yaml.safe_load(open(common_config_file, encoding="utf-8"))
    return common_config


setting_provider = None


def load_property():
    global setting_provider
    if setting_provider is None:
        from service.property_provider_service import ApplicationSettings, ApplicationContainer, ReportSettings
        setting_provider = ApplicationContainer().setting_provider()
    return setting_provider


def make_data_file_path(file_path: str, sub_dirs: List[str] = None) -> str:
    load_property()
    local_test_data_path = ""
    if platform.system() == "Windows":
        file_path = file_path.replace("/", "\\")[1:]
        local_test_data_path = setting_provider.report.local_test_data_path
    file_path = os.path.join(local_test_data_path, file_path)
    if sub_dirs is not None:
        for dir_name in sub_dirs:
            file_path = os.path.join(file_path, dir_name)
    return file_path
