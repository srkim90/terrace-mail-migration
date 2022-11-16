import os
from typing import List

from models.user_models import User
from utils.utills import make_data_file_path


class MailGzipService:
    def __init__(self, base_dir: str) -> None:
        super().__init__()
        self.base_dir = base_dir

    def run(self):
        for user in self.__get_user_data():
            mails = []
            for mail in user.messages:
                mails.append(mail.full_path)
            _mcache_db = os.path.join(make_data_file_path(user.message_store, mails), "_mcache.db")
            _mbackup_db = os.path.join(make_data_file_path(user.message_store, mails), "_mbackup.db")
            continue


    def __get_user_data(self) -> List[User]:
        for file_name in os.listdir(self.base_dir):
            full_path = os.path.join(self.base_dir, file_name)
            if "user_" not in full_path or ".json" not in full_path:
                continue
            with open(full_path, "rb") as fd:
                yield User.from_json(fd.read())
