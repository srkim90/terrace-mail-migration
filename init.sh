#!/bin/bash

CENTOS_VER=`cat /etc/redhat-release  | awk -F 'release' '{print $2}' | tr -d ' ' | cut -d '.' -f 1`
if [ ${CENTOS_VER} == 6 ]; then
    PYTHON_VER=3.6.15
elif [ ${CENTOS_VER} == 7 ]; then
    PYTHON_VER=3.9.14
else
    echo "Error. Invalid CensOS version!!"
    echo "only support CentOS 6 or 7"
    exit
fi
BASE_DIR="/opt/terrace-mail-migration"
BASE_PYTHON_DIR=./binary
PYTHON_TAR_FILE_NAME=Python-${PYTHON_VER}-minimum.tar.gz
PYTHON_TAR_FILE_PATH=${BASE_PYTHON_DIR}/${PYTHON_TAR_FILE_NAME}
PYTHON_PATH=${BASE_PYTHON_DIR}/Python-${PYTHON_VER}-minimum
PYTHON_BIN=${PYTHON_PATH}/python

if [ ! -d $BASE_PYTHON_DIR ]; then
  echo "workdir not exit ${BASE_PYTHON_DIR}"
  exit
fi

if [ ! -e $PYTHON_TAR_FILE_PATH ]; then
    if [ ! -e $PYTHON_BIN ]; then
        echo "The python installation file does not exist : ${PYTHON_TAR_FILE_PATH}"
    else
        echo "Python is already installed : $PYTHON_BIN"
    fi
  exit
fi


source $BASE_DIR/common.sh

if [ ! -e $PYTHON_BIN ]; then
    check
    echo "Python-${PYTHON_VER} does not exist. Install"
    cd ${BASE_PYTHON_DIR}
    tar -zxf $PYTHON_TAR_FILE_NAME
    ln -s Python-${PYTHON_VER}-minimum Python-minimum
    cd ..
    size=`du ${PYTHON_PATH} --max-depth=0 -h | awk '{print $1}'`
    echo "Install complete : size=${size}"
fi
