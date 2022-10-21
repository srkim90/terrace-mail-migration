
check() {
    USER=`id | grep mailadm | wc -l`
    if [ $USER != "1" ]; then
        echo "Please run it as mailadm account"
        exit
    fi
}
