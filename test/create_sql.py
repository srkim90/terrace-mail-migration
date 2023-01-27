
datefile_path = "C:\\Users\\DAOU\\Desktop\\c2_ap1_attach_id_sorted_result.txt"
sql_path = "C:\\Users\\DAOU\\Desktop\\c2_ap1_attach_id.sql"

g_all_sql = ""
def make_sql(in_item: list):
    global g_all_sql
    if len(in_item) == 0:
        return
    in_str = ""
    for item in in_item:
        in_str += "%d," % (item,)
    in_str = in_str[0:-1]
    sql = "SELECT COUNT(*) FROM GO_ATTACH_FILES WHERE ID IN (%s) AND CREATED_AT > '2022-01-01';" % in_str
    g_all_sql += sql + "\n"

def main():
    attach_ids = []
    with open(datefile_path, "r") as fd:
        lines = fd.read().split("\n")
    for line in lines:
        try:
            attach_ids.append(int(line))
        except Exception:
            pass
    in_item = []
    for attach_id in attach_ids:
        in_item.append(attach_id)
        if len(in_item) > 250:
            make_sql(in_item)
            in_item = []
    make_sql(in_item)
    print(g_all_sql)
    with open(sql_path, "w") as fd:
        fd.write(g_all_sql)
    return

if __name__ == '__main__':
    main()