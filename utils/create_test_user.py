import json

import requests


def make_data(user_name: str) -> bytes:
    result: str = '''
    {
    "name":"%s",
        "loginId":"%s",
        "password":"port2093@",
        "positionId":"",
        "gradeId":"",
        "status":"online",
        "employeeNumber":"",
        "locale":"ko",
        "mailGroup":"default",
        "mailAddQuota":"0",
        "quotaWarningMode":"",
        "quotaWarningRatio":"90",
        "quotaViolationAction":"",
        "quotaOverlookRatio":"10",
        "webFolderAddQuota":"0",
        "forwardingUse":"",
        "forwardingMode":"none",
        "mailSenderUse":"",
        "sendAllowMode":"group",
        "maxSendMailCountUse":"group",
        "maxSendMailCount":"100",
        "inboxExpireDays":"none",
        "trashExpireDays":"none",
        "spamExpireDays":"none",
        "approvalPassword":"",
        "approvalLevel":"10",
        "hiddenForwardingMode":"off",
        "mailExpireDate":"",
        "userVirtualDomains":"",
        "repUserEmail":"%s@srkim.kr",
        "directTel":"",
        "mobileNo":"",
        "webmailUsed":true,
        "popUsed":true,
        "imapUsed":true,
        "smtpAuthUsed":true,
        "additions":{
            "enName":"",
            "jpName":"",
            "zhcnName":"",
            "zhtwName":"",
            "viName":""
        },
        "groupMembers":[
        ],
        "deptMembers":[
        {
            "deptId":16883
        }
        ],
            "attPhoto":null,
            "approvalAttPhoto":null,
            "alternateAddr":[
            ],
            "alternateUserDomain":[
            ],
            "forwardingAddr":[
            ],
            "sendAllowAddr":[
            ],
            "hiddenForwardingAddr":[
            ],
            "mailSenders":[
            ],
            "configs":[
            {
                "name":"useAbbroadIpCheck",
                "value":"fasle",
                "valueType":"boolean"
            },
            {
                "name":"otpService",
                "value":"false",
                "valueType":"boolean"
            }
            ],
                "birthday":"",
                "lunarCal":false
    }
    ''' % (user_name, user_name, user_name)
    return json.dumps(json.loads(result.encode('utf-8'))).encode('utf-8')


def main():
    domaion = "https://nstaging.daouoffice.com:8443"
    data = {}
    sess = requests.session()
    result = sess.post(domaion + "/go/ad/api/login",
                       data=b'{"username":"srkim100","password":"port2093@","returnUrl":""}',
                       headers={"Content-Type": "application/json"})
    for idx in range(200):
        data = make_data("srkim%d" % (134+idx,))
        result = sess.post(domaion + "/go/ad/api/user", data=data, headers={"Content-Type": "application/json"})
        print("status: %d, result.text=\n%s" % (result.status_code, result.text))


if __name__ == "__main__":
    main()
