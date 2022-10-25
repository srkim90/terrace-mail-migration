#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
__END_DATE=`date "+%Y-%m-%d" --date "365 days ago"`
__START_DATE=`date "+%Y-%m-%d" --date "15000 days ago"` # START_DATE 는 1975년 밑으로 내려가지 않도록 할 것!
REPORT_DIR=report_`date "+%Y%m%d_%H%M%S"`

source $BASE_DIR/common.sh

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
    ./mail-scan.sh ${REPORT_DIR} $__END_DATE $__START_DATE
    ./mail-migration.sh ${REPORT_DIR}
}

main $@
