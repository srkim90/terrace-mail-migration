from service.sqlite_connector_service import SqliteConnector

'''
 버그 일시 : 2022-12-03T20:35:01.063921 ~  2022-12-03T22:22:13.827755
 버그 내용 : 클러스트#2 mail1 장비에서 스캔 도중 간혈적으로 다음 에러가 찍힌다.
 버그 싱세 : 
             Exception in thread Thread-8:
            Traceback (most recent call last):
              File "/opt/terrace-mail-migration/binary/Python-minimum/Lib/threading.py", line 916, in _bootstrap_inner
                self.run()
              File "/opt/terrace-mail-migration/binary/Python-minimum/Lib/threading.py", line 864, in run
                self._target(*self._args, **self._kwargs)
              File "./service/pgsql_scaner_service.py", line 381, in __company_worker_th
                company = self.__add_mail_count_info(company, days)
              File "./service/pgsql_scaner_service.py", line 242, in __add_mail_count_info
                messages: List[MailMessage] = self.__mail_source_path_filter(user, sqlite.get_target_mail_list(days))
              File "./service/sqlite_connector_service.py", line 243, in get_target_mail_list
                for row in cur:
            sqlite3.OperationalError: Could not decode to UTF-8 column 'full_path' with text '/data/mdata3/261/34/6160/20190918/1568786137.193476.S=0000004109.001.������� ���������..eml'
'''

def main() -> None:
    e = SqliteConnector("C:\\Users\\DAOU\Desktop\\261_34_6160\\_mcache.db",
                    1,1,"test_company", True)
    mail_list = e.get_target_mail_list(None)
    return

if __name__ == '__main__':
    main()
