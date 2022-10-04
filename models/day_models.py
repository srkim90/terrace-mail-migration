from datetime import datetime

from dataclasses_json import dataclass_json, config
from dataclasses import dataclass, field

from marshmallow import fields
try:
    from backports.datetime_fromisoformat import MonkeyPatch
except ModuleNotFoundError as e:
    pass
MonkeyPatch.patch_fromisoformat()

@dataclass_json
@dataclass
class Days:
    start_day: datetime = field(     # 이동 시작일 : ex> 2022.01.01
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))
    end_day: datetime = field(     # 이동 종료일 : ex> 2022.08.32, Not null
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format='iso')
        ))

    def get_start_day_timestamp(self):
        return self.start_day.timestamp()

    def get_end_day_timestamp(self):
        if self.end_day is None:
            return None
        return self.end_day.timestamp()