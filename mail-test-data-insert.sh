#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
PYTHON_DIR=${BASE_DIR}/binary/Python-minimum
PYTHON=${PYTHON_DIR}/python

source $BASE_DIR/common.sh

execute_python() {
    $PYTHON ${BASE_DIR}/main/mail_sender.py $@
}

main() {
    check
    SEND_TO="srkim@abctest.co.co"
    LIMIT=250
    execute_python --count=${LIMIT} --mail-to=${SEND_TO}
}

main $@
