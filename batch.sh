#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
END_DATE=`date "+%Y-%m-%d" --date "365 days ago"`
START_DATE=`date "+%Y-%m-%d" --date "15000 days ago"` # START_DATE 는 1975년 밑으로 내려가지 않도록 할 것!
REPORT_DIR=report_`date "+%Y%m%d_%H%M%S"`

main() {
    cd ${BASE_DIR}
    ./mail-scan.sh ${REPORT_DIR} $END_DATE $START_DATE
    ./mail-migration.sh ${REPORT_DIR}
}

main $@
