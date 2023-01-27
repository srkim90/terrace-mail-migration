def main():
    with open("user_all_size.txt") as fd:
        all_data = fd.read().replace("\n", "").split(",")
    sum_value = 0
    for item in all_data:
        item = item.strip()
        if len(item) == 0:
            continue
        sum_value += int(item)
    print("%s GB" % (sum_value / (1024*1024*1024)))
    return

if __name__ == '__main__':
    main()
