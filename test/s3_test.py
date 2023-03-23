from test.s3_up_downloader import S3UpDownLoader


def main() -> None:
    file_name = 'C:\\Users\\shshr\\Documents\\Windows.iso'
    BUCKET_NAME = "srkim-bucket-20230307"
    ACCESS_KEY = "AKIARGW5VC2GQ3BFXPFW"
    SECRET_KEY = "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"
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
