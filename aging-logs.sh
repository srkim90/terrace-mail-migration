#!/bin/bash

BASE_DIR=/opt/mail-migration-data
DIR_LOG="$BASE_DIR/log"
DIR_SCAN="$BASE_DIR/report"
DIR_MIGRATION_RESULT="$BASE_DIR/migration-result"

AGING_BEFORE_LOG=30
AGING_BEFORE_SCAN=100
AGING_BEFORE_MIGRATION_RESULT=100

main() {
    echo "aging log"
    if [ -d "$DIR_LOG" ]; then
        find $DIR_LOG -name "20*.log" -mtime +$AGING_BEFORE_LOG | xargs rm -f
    fi
    echo "aging scan"
    if [ -d "$DIR_SCAN" ]; then
        find $DIR_SCAN -name "report_20*_*" -mtime +$AGING_BEFORE_SCAN | xargs rm -rf
    fi
    echo "aging migration result"
    if [ -d "$DIR_MIGRATION_RESULT" ]; then
        find $DIR_MIGRATION_RESULT -name "20*_*" -mtime +$AGING_BEFORE_MIGRATION_RESULT | xargs rm -rf
    fi
    echo end
}


main $@
