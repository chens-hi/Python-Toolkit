import os
import stat
import time
import shutil
import argparse
import filetype
import exiftool


def get_album_time(file_path):
    """
    获取相册时间(优先拍摄时间, 默认修改时间)
    :param file_path: 文件路径
    :return: 时间戳
    """

    if os.path.isfile(file_path):
        if filetype.is_image(file_path):
            with exiftool.ExifToolHelper() as exif:
                meta_list = exif.get_metadata(file_path)
                for meta in meta_list:
                    date_string = meta.get("EXIF:DateTimeOriginal")
                    if date_string:
                        try:
                            date_time = time.strptime(str(date_string), "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            return os.path.getmtime(file_path)
                        else:
                            return time.mktime(date_time)
            return os.path.getmtime(file_path)

        if filetype.is_video(file_path):
            with exiftool.ExifToolHelper() as exif:
                meta_list = exif.get_metadata(file_path)
                for meta in meta_list:
                    date_string = meta.get("QuickTime:MediaCreateDate")
                    if date_string:
                        try:
                            date_time = time.strptime(str(date_string), "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            return os.path.getmtime(file_path)
                        else:
                            return time.mktime(date_time)
            return os.path.getmtime(file_path)

    return 0.0


def organize_album_file(file_path, album_dir, move_mode=False, coverage_mode=False):
    """
    整理相册文件
    :param file_path: 文件路径
    :param album_dir: 相册目录
    :param move_mode: 移动模式
    :param coverage_mode: 覆盖模式
    :return: 状态
    """

    time_stamp = get_album_time(file_path)
    if time_stamp <= 0.0:
        return False

    time_object = time.localtime(time_stamp)
    time_format = time.strftime("%Y:%m:%d %H:%M:%S", time_object)
    time_path = os.path.join(album_dir, f"{time_object.tm_year:04}", f"{time_object.tm_mon:02}")
    if not os.path.isdir(time_path):
        os.makedirs(time_path, exist_ok=True)
    os.chmod(time_path, stat.S_IRWXG)

    full_name = os.path.basename(file_path)
    file_name, file_extension = os.path.splitext(full_name)
    target_path = os.path.join(time_path, f"{file_name}{file_extension}")

    if coverage_mode:
        try:
            if os.path.isfile(target_path):
                os.remove(target_path)
        except OSError as error:
            print(error)
        else:
            print(f"{time_format} {file_path} -> {target_path}")
            if move_mode:
                os.rename(file_path, target_path)
            else:
                shutil.copy2(file_path, target_path)
    else:
        count = 0
        while True:
            if count > 0:
                target_path = os.path.join(time_path, f"{file_name}_{count}{file_extension}")
            if os.path.isfile(target_path):
                count += 1
            else:
                break
        print(f"{time_format} {file_path} -> {target_path}")
        if move_mode:
            os.rename(file_path, target_path)
        else:
            shutil.copy2(file_path, target_path)

    return True


def organize_album_folder(organize_dir, album_dir, move_mode=False, coverage_mode=False):
    """
    整理相册文件
    :param organize_dir: 整理目录
    :param album_dir: 相册目录
    :param move_mode: 移动模式
    :param coverage_mode: 覆盖模式
    :return: 状态
    """

    try:
        if os.path.isdir(organize_dir):
            for o in os.scandir(organize_dir):
                if o.is_file():
                    organize_album_file(o.path, album_dir, move_mode, coverage_mode)
    except KeyboardInterrupt:
        print("用户取消操作!")
    else:
        print("整理目录完成!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将指定目录下的相册文件, 按年月归纳整理到不同文件夹里!")
    parser.add_argument("--wait_organize_folder", required=True, type=str, help="等待处理的目录")
    parser.add_argument("--album_storage_folder", required=True, type=str, help="相册存放的目录")
    parser.add_argument("--copy_or_move", required=False, type=bool, default=False, help="True: 拷贝到相册中 False: 移动到相册中")
    parser.add_argument("--coverage_or_backup", required=False, type=bool, default=False, help="True: 覆盖同名相册文件 False: 保留相册同名文件")
    args = parser.parse_args()
    organize_album_folder(args.wait_organize_folder, args.album_storage_folder, args.copy_or_move, args.coverage_or_backup)
