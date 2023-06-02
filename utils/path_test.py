import os
from typing import Union, List

from utils.utills import parser_dir_list


def parser_dir_list_2(paths: str) -> List[str]:
    parsed_path = []
    for path in paths.split(","):
        path = path.strip()
        if os.path.exists(path) is False:
            #print("Error. Not exist dir, check your application.yml : %s" % (path,))
            #exit()
            pass
        parsed_path.append(path)
    return parsed_path


def get_move_target_volume_path(mail_path: str, dir_separator: str) -> Union[str, None]:
    new_mdata_path = parser_dir_list_2(
        """
                      /data/mdata,
                      /data/mdata2
        """
    )
    for path in new_mdata_path:
        if len(mail_path) <= len(path):
            continue
        if path[-1] != dir_separator:
            path += dir_separator
        org_path = mail_path[0:len(path)]
        if path == org_path:
            return org_path
    return None


def convert_mail_dir_volume_to_same_first_hardlink(same_eml, full_new_file) -> Union[str, None]:
    # 하드링크는 동일한 볼륨 내부에만 유효하다.
    # 따라서 하드링크를 걸려는 메일의 파티션을 원본 메일과 동일하게 변경 해준다.
    dir_separator = '/'
    org_full_new_file = full_new_file
    same_eml_volume_path = get_move_target_volume_path(same_eml, dir_separator)
    new_eml_volume_path = get_move_target_volume_path(full_new_file, dir_separator)
    if same_eml_volume_path is None or new_eml_volume_path is None:
        return None
    if same_eml_volume_path == new_eml_volume_path:
        return full_new_file
    full_new_file = full_new_file.replace(new_eml_volume_path, "")
    if full_new_file[0] == dir_separator:
        full_new_file = full_new_file[1:]
    full_new_file = os.path.join(same_eml_volume_path, full_new_file)
    file_name = full_new_file.split(dir_separator)[-1]
    dir_name = full_new_file.replace(file_name, "")
    try:
        if os.path.exists(dir_name) is False:
            os.makedirs(dir_name)
    except PermissionError:
        print(
            "[__convert_mail_dir_volume_to_same_first_hardlink] same_eml: %s, full_new_file: %s, same_eml_volume_path: %s, new_eml_volume_path: %s, org_full_new_file: %s, file_name: %s, dir_name:%s" %
            (same_eml, full_new_file, same_eml_volume_path, new_eml_volume_path, org_full_new_file, file_name,
             dir_name))
        raise PermissionError
    return full_new_file


def make_file_volume_same(copy_from: str, copy_to: str) -> str:
    if len(copy_from) < 15 or len(copy_to) < 15:
        return copy_to
    if '/data/mdata' not in copy_from or '/data/mdata' not in copy_to:
        return copy_to
    from_a = copy_from.split("/")[1]
    from_b = copy_from.split("/")[2]
    to_a = copy_to.split("/")[1]
    to_b = copy_to.split("/")[2]

    if from_a == to_a and from_b == to_b:
        return copy_to
    new_to = copy_to.replace("/%s/%s" % (to_a, to_b), "/%s/%s" % (from_a, from_b))
    f_name = new_to.split('/')[-1]
    new_dir = new_to.replace("/%s" % f_name, "")
    # print("new_dir=%s" % new_dir)
    if os.path.exists(new_dir) is False:
        os.makedirs(new_dir)
    elif os.path.isdir(new_dir) is False:
        return copy_to
    return new_to


def main():
    a = "/data/mdata/69/740/74252/20230428/1682656979.993051.S=0000040340.001.jmye@anse.co.kr.eml"
    b = "/data/mdata2/69/794/794/20230428/1682656979.993051.S=0000040340.001.jmye@anse.co.kr.eml"
    c = convert_mail_dir_volume_to_same_first_hardlink(b, a)
    print(c)


if __name__ == "__main__":
    main()
