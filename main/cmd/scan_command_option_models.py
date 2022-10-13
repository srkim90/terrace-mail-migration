from typing import Union, List

from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class ScanCommandOptions:
    application_yml_path: Union[str, None]
    target_company_ids: Union[List[int], None]

