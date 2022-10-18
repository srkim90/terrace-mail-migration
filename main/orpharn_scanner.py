import os

from common_import import *
from main.cmd.command_line_parser import read_orphan_options
from models.orphan_scan_models import OrphanScanModels
from service.orphan_scan_service import OrphanScanService
from service.property_provider_service import application_container, ApplicationSettings
from utils.utills import set_property_path


def main():
    set_property_path(read_orphan_options().application_yml_path)
    setting_provider: ApplicationSettings = application_container.setting_provider
    report_save_path = os.path.join(setting_provider.report.report_path, "orphan-scan-result.json")
    e = OrphanScanService()
    scan: OrphanScanModels = e.detect()
    report_str = scan.save_as_json(report_save_path)
    print("report save at : %s" % (report_save_path,))
    print("report_str     : \n%s" % (report_str,))
    return


if __name__ == "__main__":
    main()
