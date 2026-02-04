import os
import sys

# Detect OS
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')

if IS_MACOS:
    HE60_ROOT = '/Applications/HE60.app/Contents/backend/'
    HE60_EXE = 'HydroLight6'
    HE60_DATA = os.path.join(os.path.expanduser('~'), 'Documents', 'HE60')
# elif IS_WINDOWS:
#     HE60_ROOT = 'C:\\Program Files\\HE60\\backend\\'
#     HE60_EXE = 'HydroLight6.exe'
#     HE60_DATA = os.path.join(os.path.expanduser('~'), 'Documents', 'HE60')
# elif IS_LINUX:
#     HE60_ROOT = '/usr/local/he60/backend/'
#     HE60_EXE = 'HydroLight6'
#     HE60_DATA = os.path.join(os.path.expanduser('~'), 'Documents', 'HE60')
else:
    raise RuntimeError(f"pyhe60 is currently not supported on {sys.platform}. "
                       "Supported platform(s): MacOS.")


HE60_INPUT_DIR = os.path.join(HE60_DATA, 'run', 'batch')
HE60_OUTPUT_DIR = os.path.join(HE60_DATA, 'output', 'Hydrolight', 'excel')
