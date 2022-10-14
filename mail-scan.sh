#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
PYTHON_DIR=${BASE_DIR}/binary/Python-minimum
PYTHON=${PYTHON_DIR}/python
YML_PATH=${BASE_DIR}/profile/application.yml

print_help() {
    echo -e "\n"
    echo '================================================================================================================'
    echo ' [USAGE]'
    echo '  ./mail-scan.sh                                                                 # 모든 메일 스켄, 임의저장'
    echo '  ./mail-scan.sh [scan-data-save-directory] [end-day] [start-day] [company-id]   # 날짜범위 & 지정된 회사'
    echo '  ./mail-scan.sh [scan-data-save-directory] [end-day] [start-day]                # 날짜범위'
    echo '  ./mail-scan.sh [scan-data-save-directory] [list-of-company-id]                 # 지정된 회사'
    echo '----------------------------------------------------------------------------------------------------------------'
    echo ' [EXAMPLE]'
    echo '  ./mail-scan.sh report_20221014_142059 2022-10-14 2020-01-01 10,11,12,13,14'
    echo '  ./mail-scan.sh report_20221014_142059 2022-10-14 2020-01-01'
    echo '  ./mail-scan.sh report_20221014_142059 10'
    echo '  ./mail-scan.sh'
    echo '----------------------------------------------------------------------------------------------------------------'
    echo ' [CONFIGURATION]'
    echo "   -> configuration-path : $YML_PATH"
    #echo '----------------------------------------------------------------------------------------------------------------'
    #cat $YML_PATH
    #echo
    echo '================================================================================================================'
    echo -e "\n"

}

execute_python() {
    $PYTHON ${BASE_DIR}/main/mail_scanner.py $@
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
    if [ "$1" == "" ]; then
        execute_python
    elif [ "$1" != "" ] && [ "$2" != "" ] && [ "$3" == "" ]; then
        SAVE_DIRECTORY="--scan-data-save-directory=$1"
        COMPANY_ID="--company-id=${2}"
        execute_python --application-yml-path=$YML_PATH $COMPANY_ID $SAVE_DIRECTORY
    elif [ "$1" != "" ] && [ "$2" != "" ] && [ "$3" != "" ] && [ "$4" == "" ]; then
        SAVE_DIRECTORY="--scan-data-save-directory=$1"
        END_DAY="--end-day=${2}"
        START_DAY="--start-day=${3}"
        execute_python --application-yml-path=$YML_PATH $END_DAY $START_DAY $SAVE_DIRECTORY
    elif [ "$1" != "" ] && [ "$2" != "" ] && [ "$3" != "" ] && [ "$4" != "" ]; then
        SAVE_DIRECTORY="--scan-data-save-directory=$1"
        END_DAY="--end-day=${2}"
        START_DAY="--start-day=${3}"
        COMPANY_ID="--company-id=${4}"
        execute_python --application-yml-path=$YML_PATH $END_DAY $START_DAY $COMPANY_ID $SAVE_DIRECTORY
    else
        print_help
    fi
}

main $@