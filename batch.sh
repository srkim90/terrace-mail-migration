#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
END_DATE=`date "+%Y:%m:%d" --date "0 days ago"`
START_DATE=`date "+%Y:%m:%d" --date "7 days ago"`
REPORT_DIR=report_`date "+%Y%m%d_%H%M%S"`

main() {
    cd ${BASE_DIR}
    ./mail-scan.sh ${REPORT_DIR} $END_DATE $START_DATE
    ./mail-migration.sh ${REPORT_DIR}
}

main $@
