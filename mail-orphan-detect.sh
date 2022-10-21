#!/bin/bash

BASE_DIR=/opt/terrace-mail-migration
PYTHON_DIR=${BASE_DIR}/binary/Python-minimum
PYTHON=${PYTHON_DIR}/python
#YML_PATH=${BASE_DIR}/profile/application.yml
#export __YML_PATH="/home/mailadm/tmp/test-yml/application-move-to-old.yml" # 이관 한 데이터 다시 원래 디렉토리로 이동
export __YML_PATH="/home/mailadm/tmp/test-yml/application-move-to-new.yml" # 이관

source $BASE_DIR/common.sh

check_env() {
    if [ "$__YML_PATH" != "" ]; then
        YML_PATH=$__YML_PATH
    fi
}

execute_python() {
    $PYTHON ${BASE_DIR}/main/orpharn_scanner.py $@
}

init() {
    cd ${BASE_DIR}
    ./init.sh
}

main() {
    check
    init
    check_env
    execute_python
}

main $@
