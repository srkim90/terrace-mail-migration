import signal
import time

from service.logging_service import LoggingService
from service.property_provider_service import application_container
from utils.utills import is_windows


def signal_handler(signum: int, frame):
    logger: LoggingService = application_container.logger
    logger.info("signal 신호를 수신했습니다 : signum=%d, frame=%s" % (signum, frame))
    print("!!!!!!!!!!!!!!!!!!!!!!\n")
    exit()
    return


def install_signal():
    return
    if is_windows() is True:
        handle_signals = [signal.SIGINT]
    else:
        handle_signals = [signal.SIGINT, signal.SIGKILL, signal.CTRL_C_EVENT, signal.SIGUSR1, signal.SIGUSR2]
    for signum in handle_signals:
        signal.signal(signum, signal_handler)
