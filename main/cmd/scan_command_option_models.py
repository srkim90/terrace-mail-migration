from typing import Union, List

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from models.day_models import Days


@dataclass_json
@dataclass
class ScanCommandOptions:
    scan_range: Days
    rr_index: Union[int, None]
    scan_data_save_dir: Union[str, None]
    application_yml_path: Union[str, None]
    target_company_ids: Union[List[int], None]
    exclude_company_ids: Union[List[int], None]

