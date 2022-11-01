#!/srkim/anaconda3/bin/python

import os
import platform
import subprocess
import sys
import threading
import time
import traceback

from dataclasses import dataclass
from typing import Union, List, Tuple

from dataclasses_json import dataclass_json
from pyffmpeg import FFprobe


@dataclass_json
@dataclass
class VideoModels:
    file_name: str
    origin_codec: str
    origin_bit_rate: int
    dimensions_x: int
    dimensions_y: int


def str_stack_trace() -> str:
    type, value, tb = sys.exc_info()
    ex_traceback = ""
    for line in traceback.format_exception(type, value, tb):
        ex_traceback += "%s" % (line,)
    return ex_traceback


class VideoEncoder:
    def __init__(self, base_dir: str) -> None:
        super().__init__()
        self.WORK_THREAD_COUNT = 6
        self.check_ext = ["mp4", "avi", "mkv"]
        self.check_codec = ["h264", 'hevc']
        self.base_dir = base_dir
        self.lock = threading.Lock()
        self.queue: List[VideoModels] = []
        self.h_threads = []
        self.__init_threads()

    def __init_threads(self):
        for idx in range(self.WORK_THREAD_COUNT):
            h_thread = threading.Thread(target=self.__work_thread, args=(idx,))
            h_thread.daemon = True
            h_thread.start()
            self.h_threads.append(h_thread)

    def __os_ok(self, f_name: str, check_encode: str) -> bool:
        meta_at = self.__get_video_meta_cmd(f_name)
        if meta_at is None:
            return False
        try:
            codec: str = meta_at["codec"].lower()
        except KeyError:
            return False
        if codec == check_encode:
            return True
        return False

    def __get_video_meta(self, f_name: str) -> Union[dict, None]:
        if f_name.split(".")[-1].lower() not in self.check_ext:
            return None
        if os.path.exists(f_name) is False:
            return None
        try:
            fp = FFprobe(f_name)
        except Exception:
            return None
        meta_at = None
        for __meta_at in fp.metadata:
            if type(__meta_at) is not list:
                __meta_at = [__meta_at, ]
            for __meta_at_2 in __meta_at:
                if 'dimensions' not in __meta_at_2.keys():
                    continue
                meta_at = __meta_at_2
                break
            if meta_at is not None:
                break
        return meta_at

    @staticmethod
    def __get_dimensions_xy(line) -> Union[str, None]:
        for item in line.split(" "):
            item: str
            if 'x' not in item:
                continue
            item_split = item.split("x")
            if len(item_split) != 2:
                continue
            try:
                x = int(item_split[0])
                y = int(item_split[1])
            except Exception:
                continue
            return "%dx%d" % (x,y)
        return None

    def __check(self, f_name: str) -> Union[VideoModels, None]:
        try:
            meta_at = self.__get_video_meta_cmd(f_name)
        except Exception as e:
            return None
        if meta_at is None:
            return None
        try:
            codec: str = meta_at["codec"]
            dimensions_x: int = int(meta_at["dimensions"].split("x")[0])
            dimensions_y: int = int(meta_at["dimensions"].split("x")[1])
            data_rate: int = int(meta_at["data_rate"].replace("kb/s", "").strip())
        except KeyError:
            return None
        if codec.lower() not in self.check_codec:
            print("unsupperted codec: %s" % codec)
            return None
        return VideoModels(
            file_name=f_name,
            origin_codec=codec.lower(),
            origin_bit_rate=data_rate,
            dimensions_x=dimensions_x,
            dimensions_y=dimensions_y
        )

    def __work_thread(self, idx):
        while True:
            self.lock.acquire()
            if self.queue is None:
                self.lock.release()
                break
            if len(self.queue) == 0:
                self.lock.release()
                time.sleep(1.0)
                continue
            model: VideoModels = self.queue[0]
            self.queue = self.queue[1:]
            self.lock.release()
            self.__encode(model)

    def __encode_enqueue(self, model: VideoModels):
        while True:
            self.lock.acquire()
            if len(self.queue) > self.WORK_THREAD_COUNT:
                self.lock.release()
                time.sleep(1.0)
                continue
            self.queue.append(model)
            self.lock.release()
            break

    def __select_input_codec(self, origin_codec):
        if origin_codec == "h264":
            return "h264_cuvid"
        elif origin_codec == "hevc" or origin_codec == "h265":
            return "hevc_cuvid"
        else:
            raise IOError("not supported input codec : %s" % origin_codec)

    def __select_bit_rate(self, model: VideoModels) -> int:
        ratio_codec = 1.0
        bit_rate_pair: List[Tuple[int, float]] = [
            (1000, 2.5),
            (2500, 2.0),
            (4000, 1.75),
            (6000, 1.5),
            (8000, 1.25),
            (10000, 1.0),
        ]
        ratio_org_bit_rate = 1.0
        if model.origin_codec == "h264":
            ratio_codec = 0.4
        elif model.origin_codec == "hevc" or model.origin_codec == "h265":
            ratio_codec = 0.35
        for pair in bit_rate_pair:
            check_bit = pair[0]
            check_rate = pair[1]
            if model.origin_bit_rate < check_bit:
                ratio_org_bit_rate = check_rate
                break
        ratio = ratio_codec * ratio_org_bit_rate
        if ratio > 1.0:
            ratio = 1.0
        return int(model.origin_bit_rate * ratio)

    def __make_ffmpeg_cmd(self, model: VideoModels) -> (str, str):
        tmp_file_suffix = "tmp." + model.file_name.split(".")[-1]
        new_file_name = "%s.%s" % (model.file_name, tmp_file_suffix)
        org_file_name = model.file_name
        input_codec = self.__select_input_codec(model.origin_codec)
        output_codec = "hevc_nvenc"
        bit_rate = self.__select_bit_rate(model)
        cmd: List[str] = []

        cmd.append("ffmpeg")
        cmd.append("-hwaccel cuvid")
        cmd.append("-c:v %s" % (input_codec,))
        cmd.append("-i '%s'" % (org_file_name,))
        cmd.append("-movflags use_metadata_tags")
        #cmd.append("-map 0")
        #cmd.append("-copy_unknown")
        #cmd.append("-c copy")
        cmd.append("-map_metadata 0")
        cmd.append("-c:v %s" % (output_codec,))
        cmd.append("-vtag hvc1")
        cmd.append("-b:v %dk" % (bit_rate,))
        cmd.append("'%s'" % new_file_name)

        cmd_text = ""
        for item in cmd:
            cmd_text += "%s " % (item,)
        return cmd_text, new_file_name

    def __encode(self, model: VideoModels):
        try:
            self.__encode_in(model)
        except Exception as e:
            print("Error. __encode : %s\n%s" % (e, str_stack_trace()))
            return

    def __encode_in(self, model: VideoModels):
        cmd, new_file_name = self.__make_ffmpeg_cmd(model)
        print(cmd)
        if os.path.exists(new_file_name) is True:
            os.remove(new_file_name)
        subprocess.run(cmd, shell=True)
        if self.__os_ok(new_file_name, "hevc") is True:
            stat = os.stat(model.file_name)
            os.utime(new_file_name, (stat.st_atime, stat.st_mtime))
            os.remove(model.file_name)

            f_ext = model.file_name.split(".")[-1]
            f_name = model.file_name.replace(".%s" % f_ext, "")
            file_name = "%s_hevc.%s" % (f_name, f_ext)
            os.rename(new_file_name, file_name)

        return

    def scan(self):
        for (root, dirs, files) in os.walk(self.base_dir):
            if len(files) > 0:
                for file_name in files:
                    file_name: str
                    if "_hevc." in file_name.lower() or '.tmp.' in file_name:
                        continue
                    full_path = os.path.join(root, file_name)
                    if os.stat(full_path).st_size < 1024 * 1024 * 10:
                        continue
                    model: VideoModels = self.__check(full_path)
                    if model is not None:
                        self.__encode_enqueue(model)
        while len(self.queue) > 0:
            time.sleep(1.0)
        self.queue = None
        for h_thread in self.h_threads:
            h_thread.join()
        return

    @staticmethod
    def __get_video_meta_cmd(f_name: str) -> Union[dict, None]:
        cmd = ["ffprobe", "%s" % (f_name,)]
        fd_popen = subprocess.Popen(cmd, stderr=subprocess.PIPE).stderr
        data = fd_popen.read().strip().decode("utf-8")
        fd_popen.close()
        for line in data.split("\n"):
            line = line.lower()
            if "stream" in line and "video" in line:
                codec = line.split("video: ")[1].split(" ")[0]
                data_rate = line.split(" kb/s")[0].split(" ")[-1] + " kb/s"
                #dimensions = line.split(',')[3].split(" ")[1]
                dimensions = VideoEncoder.__get_dimensions_xy(line)
                return {
                    "codec": codec,
                    "data_rate": data_rate,
                    "dimensions": dimensions
                }
        return None



    def test(self, ):
        self.__get_video_meta_cmd("")


def main():
    if platform.system() == "Linux":
        dir = "./"
    else:
        dir = "./"
    e = VideoEncoder(dir)
    e.scan()



if __name__ == "__main__":
    main()
