import os
import sys
from clang.cindex import Config


def init_clang():
    if not Config.loaded:
        Config.set_library_file(get_libclang_path())


def get_libclang_path():
    try:
        return os.environ['LIBCLANG']
    except KeyError:
        return get_default_libclang_path()


def get_default_libclang_path():
    if sys.platform == 'darwin':
        return '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/libclang.dylib'
    else:
        return '/usr/lib/libclang.so'


def get_ccflags():
    try:
        return os.environ['CCFLAGS']
    except KeyError:
        return ['--std=c++14']
