import hashlib
import os
import sys


def calculate_checksum(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        content = f.read()
    checksum = hashlib.md5(content).hexdigest()  # 또는 sha1, sha256 등 다른 해시 알고리즘 사용 가능
    return checksum


def main():
    file_a = sys.argv[1]
    file_b = sys.argv[2]
    stat_a: os.stat_result = os.stat(file_a)
    stat_b: os.stat_result = os.stat(file_b)
    checksum_a = calculate_checksum(file_a)
    checksum_b = calculate_checksum(file_b)
    print("same=%s, checksum_a=%s(%d byte, %s link), "
          "checksum_b=%s(%d byte, %s link)" % ((checksum_b == checksum_a),
                                               checksum_a, stat_a.st_size, stat_a.st_ino,
                                               checksum_b, stat_b.st_size, stat_b.st_ino))


if __name__ == "__main__":
    main()
