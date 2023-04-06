import pymysql


def main():
    conn: pymysql.connect = pymysql.connect(host='192.168.102.82',
                           user='root',
                           password='MOBIGEN_PASS',
                           db='glance',
                           charset='utf8')

    #NAME = "aaa" #raw_input("Enter the instance name: ")

    sql = "select id,name from images where status='active'"
    with conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchall()

            for data in result:
                print(data)


if __name__ == "__main__":
    main()
