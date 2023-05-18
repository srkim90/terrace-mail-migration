

import imaplib

def main():
    #mail_addr_1 = "srkim@itzy.daouoffice.com"
    mail_addr_1 = "srkim90@domain-test-1.srkim.kr"
    #mail_addr_1 = "srkim@daou.co.kr"
    #mail_addr_1 = "mailadm@itzy.daouoffice.com"
    #server_ip = "portal.daou.co.kr"
    server_ip = '172.22.1.138'
    server = imaplib.IMAP4_SSL(server_ip)
    #server.authenticate()
    server.login(mail_addr_1, '')


if __name__ == "__main__":
    main()
