from enum import Enum, auto

'''
    MailMigrationFailType: 개별 메일의 마이그레이션 실패 코드
        --> 실패 시, 해당 메일만 SKIP 처리 된다.
'''
class MailMigrationResultType(str, Enum):
    SUCCESS = "SUCCESS"                                                                 # 성공
    NOT_MATCH_SIZE = "NOT_MATCH_SIZE"                                                   # scan시 확인한 메일 크기와 다르다.
    ALREADY_REMOVED = "ALREADY_REMOVED"                                                 # scan시 확인한 mid/uid값이 사용자 메일 DB에 없다! (스캔과 이관 사이에 사용자가 메일을 지웠다!)
    ORIGINAL_DIR_NOT_IN_APPLICATION_YML = "ORIGINAL_DIR_NOT_IN_APPLICATION_YML"         # 원본 메일 경로가 application.yml에서 지정 한 경로 목록에 포함 되어 있지 않습니다.
    NOT_EXIST_MOVE_TARGET_DIR = "NOT_EXIST_MOVE_TARGET_DIR"                             # 이동 대상 디렉토리가 유효하지 않습니다.
    ALREADY_EXIST_FILE_IN_MOVE_TARGET_DIR = "ALREADY_EXIST_FILE_IN_MOVE_TARGET_DIR"     # 이동 대상 디렉토리에 동일한 이름의 메일이 이미 존재 합니다.
    SQLITE_M_CACHE_DB_SELECT_FAIL = "SQLITE_M_CACHE_DB_SELECT_FAIL"                     # _mcache.db 에서 메일 가져오기 select 쿼리가 실패했다.
    SQLITE_M_CACHE_DB_UPDATE_FAIL = "SQLITE_M_CACHE_DB_UPDATE_FAIL"                     # _mcache.db 에서 메일 경로 update 쿼리가 실패했다.
    SQLITE_M_BACKUP_DB_UPDATE_FAIL = "SQLITE_M_BACKUP_DB_UPDATE_FAIL"                   # _mbackup.db 에서 메일 경로 update 쿼리가 실패했다.
    SQLITE_M_CACHE_DB_VALIDATE_FAIL = "SQLITE_M_CACHE_DB_VALIDATE_FAIL"                 # _mcache.db 에서 메일 없데이트 이후 검증하기위해 select 쿼리를 날리는데, 값이 정상적으로 업데이트 되지 않았다.
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"                                               # 정의되지 않는 에러

'''
    UserMigrationFailType: 특성 사용자의 메일의 마이그레이션 실패 코드
        --> 실패 시, 해당 사용자 메일 전체를 마이그레이션 하지 않는다.
'''
class UserMigrationResultType(str, Enum):
    SUCCESS = "SUCCESS"                                                                 # 성공
    NOT_EXIST_M_CACHE_DB = "NOT_EXIST_M_CACHE_DB"                                       # _mcache.db가 존재하지 않는다. (해당 메일 마이그레이션 시작 X)
    NOT_EXIST_M_BACKUP_DB = "NOT_EXIST_M_BACKUP_DB"                                     # _mbackup.db가 존재하지 않는다. (해당 메일 마이그레이션 시작 X)
    FAIL_TO_COMMIT_M_CACHE_DB = "FAIL_TO_COMMIT_M_CACHE_DB"                             # _mcache.db 커밋에 실패 하였다. (원본 메일 보존하고, 이관된 메일을 지운다)
    FAIL_TO_COMMIT_M_BACKUP_DB = "FAIL_TO_COMMIT_M_BACKUP_DB"                           # _mbackup.db 커밋에 실패 하였다. (원본 메일 보존하고, 이관된 메일을 지운다)
