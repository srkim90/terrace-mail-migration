from typing import Union, List

from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class OrphanCommandOptions:
    application_yml_path: Union[str, None]

