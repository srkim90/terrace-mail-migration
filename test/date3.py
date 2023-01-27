import datetime
import json


def main():
    first_add_on = {}
    with open("C:\\Users\\DAOU\\Desktop\\full_path.txt", "rb") as fd:
        data_all = fd.read().split(b"\n")
    for idx, item in enumerate(data_all):
        if len(item) < 8:
            continue
        try:
            item = item.decode("utf-8")
        except Exception as e:
            continue
        split = item.split("/")
        yyyymmdd = int(split[6])
        mdata = split[2]
        try:
            if first_add_on[mdata] > yyyymmdd:
                first_add_on[mdata] = yyyymmdd
        except:
            first_add_on[mdata] = yyyymmdd
        #if idx == 100000:
        #    break
    print("%s" % json.dumps(first_add_on, indent=4))
    return

if __name__ == '__main__':
    main()
