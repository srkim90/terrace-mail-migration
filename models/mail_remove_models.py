from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class MailRemoveModels:
    folder_no: int
    uid_no: int
    del_full_path: str
    new_full_path: str
    msg_size: int
    is_webfolder: bool
