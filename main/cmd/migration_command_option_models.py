from typing import Union, List

from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class MigrationCommandOptions:
    target_company_ids: Union[List[int], None]
    target_user_ids: Union[List[int], None]
    target_scan_data: Union[str, None]
    application_yml_path: Union[str, None]

