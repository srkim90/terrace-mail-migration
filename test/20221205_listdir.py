#!/opt/terrace-mail-migration/binary/Python-minimum/python
import os


def main() -> None:
    target_dir = "/data/mdata3/261/34/6160/20190918"
    for item in os.listdir(target_dir):
        print("%s" % type(item))
    return

if __name__ == '__main__':
    main()
