#!/bin/bash

BASE_PYTHON_DIR=./binary
PYTHON_TAR_FILE_NAME=Python-3.9.14-minimum.tar.gz
PYTHON_TAR_FILE_PATH=${BASE_PYTHON_DIR}/${PYTHON_TAR_FILE_NAME}
PYTHON_PATH=${BASE_PYTHON_DIR}/Python-3.9.14-minimum
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

if [ ! -e $PYTHON_BIN ]; then
    echo "Python 3.9 does not exist. Install"
    cd ${BASE_PYTHON_DIR}
    tar -zxf $PYTHON_TAR_FILE_NAME
    cd ..
    size=`du ${PYTHON_PATH} --max-depth=0 -h | awk '{print $1}'`
    echo "Install complete : size=${size}"
fi