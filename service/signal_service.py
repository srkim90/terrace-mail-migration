import signal
import time

from service.logging_service import LoggingService
from service.property_provider_service import application_container
from utils.utills import is_windows

g_stop_flags = False


def get_stop_flags():
    return g_stop_flags


def __signal_handler(signum: int, frame):
    global g_stop_flags
    logger: LoggingService = application_container.logger
    logger.info("signal 신호를 수신했습니다 : signum=%d, frame=%s" % (signum, frame))
    g_stop_flags = True
    return


def install_signal():
    if is_windows() is True:
        handle_signals = [signal.SIGINT]
    else:
        handle_signals = [signal.SIGINT, signal.SIGUSR1, signal.SIGUSR2]
    for signum in handle_signals:
        signal.signal(signum, __signal_handler)
