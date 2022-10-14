#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
PYTHON_DIR=${BASE_DIR}/binary/Python-minimum
PYTHON=${PYTHON_DIR}/python
YML_PATH=${BASE_DIR}/profile/application.yml

print_help() {
    echo -e "\n"
    echo '+=================================================================================================+'
    echo ' [USAGE]'
    echo '  ./mail-migration.sh [target-scan-date]'
    echo '  ./mail-migration.sh [target-scan-date] [list-of-company-id]'
    echo '  ./mail-migration.sh [target-scan-date] [list-of-company-id] [list-of-user-id]'
    echo '---------------------------------------------------------------------------------------------------'
    echo ' [EXAMPLE]'
    echo '  ./mail-migration.sh report_20221014_142059'
    echo '  ./mail-migration.sh report_20221014_142059 10,11,12,13,14'
    echo '  ./mail-migration.sh report_20221014_142059 11 34444'
    echo '---------------------------------------------------------------------------------------------------'
    echo ' [CONFIGURATION]'
    echo "   -> configuration-path : $YML_PATH"
    echo '---------------------------------------------------------------------------------------------------'
    echo ' [OPTION-DESCRIPTION]'
    echo '   -> target-scan-date     :  /opt/mail-migration-data/report 밑에 있는 스켄 결과 데이터 디렉토리'
    echo '   -> list-of-company-id   : Target company id 목록; 쉼표(,) 으로 구분, 없을 경우 전체 대상'
    echo '   -> list-of-user-id      : Target user id 목록; 쉼표(,) 으로 구분, 없을 경우 전체 대상'
    echo '+=================================================================================================+'
    echo -e "\n"

}

execute_python() {
    $PYTHON ${BASE_DIR}/main/mail_transfer.py $@
}

init() {
    cd ${BASE_DIR}
    ./init.sh
}

main() {
    init
    ### HELP 출력
    if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
        print_help
        return
    fi
    if [ "$1" != "" ] && [ "$2" == "" ]; then
        TARGET_SCAN_DATE=${1}
        execute_python --application-yml-path=$YML_PATH $TARGET_SCAN_DATE --target-scan-date=$TARGET_SCAN_DATE
    elif [ "$1" != "" ] && [ "$2" != "" ] && [ "$3" == "" ]; then
        COMPANY_ID="--company-id=${2}"
        TARGET_SCAN_DATE=${1}
        execute_python --application-yml-path=$YML_PATH $TARGET_SCAN_DATE --target-scan-date=$TARGET_SCAN_DATE $COMPANY_ID
    elif [ "$1" != "" ] && [ "$2" != "" ] && [ "$3" != "" ]; then
        USER_ID="--company-id=${3}"
        COMPANY_ID="--company-id=${2}"
        TARGET_SCAN_DATE=${1}
        execute_python --application-yml-path=$YML_PATH $TARGET_SCAN_DATE --target-scan-date=$TARGET_SCAN_DATE $USER_ID $COMPANY_ID
    else
        print_help
    fi
}

main $@
