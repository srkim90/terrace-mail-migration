#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
END_DATE=`date "+%Y-%m-%d" --date "0 days ago"`
START_DATE=`date "+%Y-%m-%d" --date "15000 days ago"`
REPORT_DIR=report_`date "+%Y%m%d_%H%M%S"`

#export __YML_PATH="/home/mailadm/tmp/test-yml/application-move-to-old.yml" # 이관 한 데이터 다시 원래 디렉토리로 이동
export __YML_PATH="/home/mailadm/tmp/test-yml/application-move-to-new.yml" # 이관

main() {
    cd ${BASE_DIR}
    ./mail-scan.sh ${REPORT_DIR} $END_DATE $START_DATE
    ./mail-migration.sh ${REPORT_DIR}
}

main $@
