from typing import List

from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class SenderCommandOptions:
    mail_to: List[str]
    n_send_mail: int
    to_all: bool

