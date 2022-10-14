from typing import Union, List

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from models.day_models import Days


@dataclass_json
@dataclass
class ScanCommandOptions:
    scan_range: Days
    application_yml_path: Union[str, None]
    target_company_ids: Union[List[int], None]

