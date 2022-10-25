#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
__END_DATE=`date "+%Y-%m-%d" --date "0 days ago"`
__START_DATE=`date "+%Y-%m-%d" --date "15000 days ago"`
REPORT_DIR=report_`date "+%Y%m%d_%H%M%S"`

source $BASE_DIR/common.sh

#export __YML_PATH="/home/mailadm/tmp/test-yml/application-move-to-old.yml" # 이관 한 데이터 다시 원래 디렉토리로 이동
export __YML_PATH="/home/mailadm/tmp/test-yml/application-move-to-new.yml" # 이관


main() {
    cd ${BASE_DIR}
    check


    if [ "$1" != "" ] && [ "$2" != "" ] && [ "$3" == "" ]; then
        __END_DATE=${1}
        __START_DAY=${2}
    elif [ "$START_DAY" != "" ] && [ "$END_DATE" != "" ]; then
        __END_DATE=${END_DATE}
        __START_DAY=${START_DAY}
    fi   
    #./mail-scan.sh ${REPORT_DIR} $__END_DATE $__START_DATE
    REPORT_DIR=report_20221025_181843
    ./mail-migration.sh ${REPORT_DIR}
}

main $@
