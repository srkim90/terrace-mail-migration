from test.s3_up_downloader import S3UpDownLoader


def main() -> None:
    file_name = 'C:\\Users\\shshr\\Documents\\Windows.iso'
    BUCKET_NAME = "srkim-bucket-20230307"
    ACCESS_KEY = "MMMMMMMMMMMMMMMMMMMM"
    SECRET_KEY = "NNNNNNNNNNNNNNNNN"
    ENDPOINT_URL = None

    s3_updownloader = S3UpDownLoader(
        bucket_name=BUCKET_NAME,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        endpoint_url=ENDPOINT_URL,
        verbose=False
    )
    s3_updownloader.upload_file(file_name, "text-path")

    s3_updownloader.download_file()


if __name__ == '__main__':
    main()
