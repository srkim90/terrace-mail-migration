import os

from models.orphan_scan_models import OrphanScanModels
from service.orphan_scan_service import OrphanScanService
from service.property_provider_service import application_container, ApplicationSettings


def main():
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
