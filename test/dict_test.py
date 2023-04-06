'''

{
    "start_at": "2023-04-01T23:22:14.245121",
    "end_at": "2023-04-01T23:22:50.031851",
    "time_consuming": 35,
    "n_migration_user_target": 14,
    "n_migration_user_success": 8,
    "n_migration_user_fail": 0,
    "n_migration_mail_target": 46323,
    "n_migration_mail_success": 0,
    "n_migration_mail_fail": 23757,
    "user_result_type_classify": {
        "SUCCESS": 8
    },
    "mail_result_type_classify": {
        "UNEXPECTED_ERROR": 23757
    },
    "company_mail_size": 19885146909,
    "counting_date_range": null
}

'''

import json


def main():
    report = {}
    report["start_at"] = "2023-04-01T23:22:14.245121"
    report["end_at"] = "2023-04-01T23:22:50.031851"
    report["time_consuming"] = 35
    report["n_migration_user_target"] = 14
    report["n_migration_user_success"] = 8
    report["n_migration_user_fail"] = 0
    report["n_migration_mail_target"] = 46323
    report["n_migration_mail_success"] = 0
    report["n_migration_mail_fail"] = 23757
    report["user_result_type_classify"] = {
        "SUCCESS": 8
    }
    report["mail_result_type_classify"] = {
        "UNEXPECTED_ERROR": 23757
    }
    report["company_mail_size"] = 19885146909
    report["counting_date_range"] = None

    json_report = json.dumps(report, indent=4, ensure_ascii=False)
    print(json_report)

    return


if __name__ == '__main__':
    main()
