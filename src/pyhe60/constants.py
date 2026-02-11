import os
import sys


def get_he60_data_dir():
    if  sys.platform.startswith('darwin'):
        return os.path.join(os.path.expanduser('~'), 'Documents', 'HE60')
    elif sys.platform.startswith('linux'):
        return os.path.join(os.path.expanduser('~'), 'he60')
    elif sys.platform.startswith('win'):
        return os.path.join(os.path.expanduser('~'), 'Documents', 'HE60')
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}. Supported platforms: MacOS, Linux, and Windows (untested).")


# Detect OS
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')

if IS_MACOS:
    HE60_WD = '/Applications/HE60.app/Contents/backend/'
    HE60_EXE = './HydroLight6'
    HE60_DATA = get_he60_data_dir()
elif IS_LINUX:
    HE60_WD = os.path.join(os.path.expanduser('~'), 'he60', 'backend')
    HE60_EXE = '/usr/local/bin/HydroLight6'
    HE60_DATA = get_he60_data_dir()
elif IS_WINDOWS:
    HE60_ROOT = 'C:\\Program Files\\HE60\\backend\\'
    HE60_EXE = 'HydroLight6.exe'
    HE60_DATA = get_he60_data_dir()
else:
    raise RuntimeError(f"pyhe60 is currently not supported on {sys.platform}. "
                       "Supported platform(s): MacOS, Linux, and Windows (untested).")


HE60_INPUT_DIR = os.path.join(HE60_DATA, 'run', 'batch')
HE60_OUTPUT_DIR = os.path.join(HE60_DATA, 'output', 'HydroLight', 'excel')