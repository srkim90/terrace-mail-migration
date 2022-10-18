

from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class OrphanScanModels:
    company_count: int              # 회사 수

    user_count: int                 # 사용자 수
    mail_user_count: int            # 메일 사용자 수
    mcache_db_count: int            # _mcache.db 개수 (파일 시스템 상의)
    mail_count: int                 # 파일 시스템 상 모든 메일 수

    orphan_user_count: int          # 회사에 속해있지 않은 사용자 수
    orphan_mail_user_count: int     # user 에 속해있지 않은 메일 계정 수
    orphan_mcache_db_count: int     # mail_user 에 집계 되지 않은 _mcache.db 파일 개수
    orphan_mail_count: int          # _mcache.db에 인덱싱이 없는 메일 수

    orphan2_mail_user_count: int    # company에 속해있지 않고, user에도 속해 있지 않은 메일 계정 수
    orphan2_mcache_db_count: int    # company에 속해있지 않고, user에도 속해 있지 않고 mail_user에도 속해 있지 않은 mcache_db 수
    orphan2_mail_count: int         # ... 최종 이동 되지 않은 메일 수


    def save_as_json(self, save_path=None):
        json_data: bytes = self.to_json(indent=4, ensure_ascii=False).encode("utf-8")
        if save_path is not None:
            with open(save_path, "wb") as fd:
                fd.write(json_data)
        return json_data.decode("utf-8")