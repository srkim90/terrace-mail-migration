import datetime
import gzip

check_file = 'D:\\data\\t4imap_log_all_20230510\\20230504.log'


def line_decode(line: bytes) -> str:
    check_encode = ['utf-8', 'euc-kr', 'cp949']
    for encode in check_encode:
        try:
            return line.decode(encode)
        except UnicodeDecodeError:
            continue
    return None


def main():
    with open(check_file, "rb") as fd:
        data_all = fd.read().split(b'\n')
    for line in data_all:
        if b'ACT:EXPUNGE' not in line:
            continue
        line = line_decode(line)
        if line is None:
            continue
        try:
            unix_timestamp = int(line.split('MID:')[1].split('.')[1][:-4])
        except ValueError:
            continue
        datetime_at = datetime.datetime.fromtimestamp(unix_timestamp)

        print("datetime_at: %s" % (datetime_at.strftime("%Y-%m-%d %H:%M:%S"),))


if __name__ == "__main__":
    main()
