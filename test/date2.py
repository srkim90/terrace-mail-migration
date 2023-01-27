import datetime


def main():
    sum_size = 0
    with open("C:\\Users\\DAOU\\Desktop\\st_size.txt") as fd:
        data_all = fd.read().split("\n")
    for idx, item in enumerate(data_all):
        if len(item) < 8:
            continue
        sum_size += int(item)
    print("sum_size : %d" % (sum_size,))
    with open("C:\\Users\\DAOU\\Desktop\\msg_receive.txt") as fd:
        data_all = fd.read().split("\n")
    all_data = {}
    for idx, item in enumerate(data_all):
        if len(item) < 8:
            continue
        item = datetime.datetime.fromtimestamp(int(item))
        key = item.strftime("%Y-%m") + "-01"
        try:
            all_data[key] += 1
        except KeyError:
            all_data[key] = 1
        #if idx == 100000:
        #    break
    for key in sorted(all_data.keys()):
        print("%s %d" % (key, all_data[key]))
    return

if __name__ == '__main__':
    main()
