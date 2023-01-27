import copy
import datetime
import json
import os

#log_path = "C:\\Users\\DAOU\\Desktop\\action.result.txt"
log_path = "C:\\Users\\DAOU\\Desktop\\action_read_message_all.log"
tmp_json_path = "C:\\Users\\DAOU\\Desktop\\action.result.json"
scan_path = "D:\\data\\20221203_203500"


def get_log_list():
    '''
        {
            domain  : {
                mail_id : {mail_id_list: [uid1, uid2, ...]}
            },
        }
    '''
    log_dict = {}
    with open(log_path, "rb") as fd:
        data_all = fd.read().split(b"\n")
    for idx, line in enumerate(data_all):
        try:
            if b"WEBMAIL" in line:
                email = line.split(b"MU:")[1].split(b" ")[0].decode("utf-8")
                uid = int(line.split(b"UID:")[1].split(b" ")[0].decode("utf-8"))
            else:
                email = line.split(b",")[0].decode("utf-8")
                uid = int(line.split(b"uid=")[1].split(b"&")[0].decode("utf-8"))
            mail_id = email.split("@")[0]
            domain = email.split("@")[1]
        except IndexError:
            continue
        try:
            company_dict = log_dict[domain]
        except KeyError:
            log_dict[domain] = {}
            company_dict = log_dict[domain]
        try:
            user_mail_list = company_dict[mail_id]
        except KeyError:
            company_dict[mail_id] = {"mail_id_list" : []}
            user_mail_list = company_dict[mail_id]
        user_mail_list["mail_id_list"].append(uid)
        # print("%s : %s" % (email, uid))
    return log_dict



def get_companies():
    '''
    {"domain_name" : company_id}
    '''
    company_id_dict = {}
    for company_id in os.listdir(scan_path):
        dir_path = os.path.join(scan_path, company_id)
        if os.path.isdir(dir_path) is False:
            continue
        for json_name in os.listdir(dir_path):
            full_name = os.path.join(dir_path, json_name)
            if "company_report_" not in full_name:
                continue
            with open(full_name, "rb") as fd:
                json_data = json.loads(fd.read())
            domain_name = json_data["domain_name"]
            company_id_dict[domain_name] = company_id
    return company_id_dict

def add_user_id(company_id, company_path, user_dict):
    for item in os.listdir(company_path):
        if "user_" not in item:
            continue
        full_json_path = os.path.join(company_path, item)
        with open(full_json_path, "rb") as fd:
            json_data = json.loads(fd.read())
        login_id = json_data["login_id"]
        user_id = json_data["id"]
        if login_id not in user_dict.keys():
            continue
        user_dict_in = user_dict[login_id]
        user_dict_in["login_id"] = login_id
        user_dict_in["user_id"] = user_id
        user_dict_in["company_id"] = company_id
    pass

def handle_a_company(company_id, domain, user_dict):
    company_path = os.path.join(scan_path, "%s" % company_id)
    add_user_id(company_id, company_path, user_dict)
    return

baseline = datetime.datetime.strptime('2022-12-15 15:00:00', '%Y-%m-%d %H:%M:%S')
check_date = []
for idx in range(36):
    #check_date.append((idx+1)*30)
    pass
check_date = [365*1, 365*2,365*3,365*4, 365*5]
classify_dict = {
    "today" : 0,
    "other" : 0
}
def time_classify(receive_date: datetime.datetime):
    diff_time = baseline - receive_date
    diff_day = diff_time.days

    for idx, check_diff in enumerate(check_date):
        if diff_day <= check_diff:
            #key_name = "within_%d_day" % check_diff
            key_name = check_diff
            try:
                classify_dict[key_name] += 1
            except KeyError as e:
                classify_dict[key_name] = 1
            break
        elif idx == len(check_date) -1:
            classify_dict["other"] += 1
    return

def handle_a_user(users, uid_list):
    ln_classify = 0
    messages = users["messages"]
    for item in messages:
        uid = item["uid_no"]
        msg_receive = item["msg_receive"]
        if uid not in uid_list:
            continue
        receive_date = datetime.datetime.fromtimestamp(msg_receive)
        time_classify(receive_date)
        ln_classify += 1
    classify_dict["today"] += len(uid_list) - ln_classify
    return

def print_result():
    within_list = []
    classify_dict_in = copy.deepcopy(classify_dict)
    classify_dict_in["today"] = int(classify_dict_in["today"]/2)
    for item in classify_dict_in.keys():
        if type(item) != int:
            continue
        within_list.append(item)
    within_list = sorted(within_list)
    print("%s\t%d" % ("1 > month", classify_dict_in["today"]))
    for idx, item in enumerate(within_list):
        mm = int(item / 30)
        print("%d ~ %d\t%d" % (mm, mm+1, classify_dict_in[item]))
    print("%s\t%d" % ("before", classify_dict_in["other"]))
    #     if "within_" not in item:
    #         continue
    #     day_nn = int(item.strip("_")[1].split("_")[0])
    #     dict_within[day_nn] = classify_dict_in[item]
    # for day_nn in classify_dict_in


    # json_str = json.dumps(classify_dict_in, indent=4)
    # print(json_str)

def handle_a_company2(domain, user_dict):
    for mail_id in user_dict.keys():
        mail_dict = user_dict[mail_id]
        if len(mail_dict.keys()) == 1:
            continue
        login_id = mail_dict["login_id"]
        user_id = mail_dict["user_id"]
        company_id = mail_dict["company_id"]
        mail_id_list = mail_dict["mail_id_list"]
        user_json_path = os.path.join(scan_path, "%s" % company_id, "user_%d.json" % user_id)
        with open(user_json_path, "rb") as fd:
            users = json.loads(fd.read())
        handle_a_user(users, mail_id_list)
    print_result()
    return


def main():
    # company_id_dict = get_companies()
    # log_dict = get_log_list()
    # total_len = len(log_dict.keys())
    # for idx,domain in enumerate(log_dict.keys()):
    #     print("[%s/%s] %s" % (idx, total_len, domain))
    #     try:
    #         company_id = company_id_dict[domain]
    #     except KeyError:
    #         continue
    #     handle_a_company(company_id, domain, log_dict[domain])
    # log_dict_json = json.dumps(log_dict, indent=4)
    # with open(tmp_json_path, "w") as fd:
    #     fd.write(log_dict_json)
    # return
    with open(tmp_json_path, "r") as fd:
        log_dict = json.loads(fd.read())

    total_len = len(log_dict.keys())
    for idx,domain in enumerate(log_dict.keys()):
        print("[%s/%s] %s" % (idx, total_len, domain))
        handle_a_company2(domain, log_dict[domain])
    return


if __name__ == '__main__':
    main()
