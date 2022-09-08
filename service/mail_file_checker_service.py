import os
import platform


class MailMessageFileChecker:
    setting_provider = None

    def __init__(self) -> None:
        super().__init__()

    def __check_setting(self):
        from service.property_provider_service import ApplicationContainer, ReportSettings
        if self.setting_provider is None:
            self.setting_provider = ApplicationContainer().setting_provider()
            self.report: ReportSettings = self.setting_provider.report

    def __make_mail_name(self, eml_path: str):
        local_test_data_path = ""
        if platform.system() == "Windows":
            eml_path = eml_path.replace("/", "\\")[1:]
            local_test_data_path = self.report.local_test_data_path
        return os.path.join(local_test_data_path, eml_path)

    def check_file_status(self, eml_path: str) -> os.stat_result:
        self.__check_setting()
        eml_path = self.__make_mail_name(eml_path)
        return os.stat(eml_path)
