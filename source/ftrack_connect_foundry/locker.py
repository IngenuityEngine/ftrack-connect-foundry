# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import stat


def lockFile(path):
    '''Lock the file at *path* preserving other flags.'''
    # Get the write bits.
    writeBits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH

    # Invert them.
    readExBits = ~writeBits

    # AND them with the original mode so that only write bits are set to 0 and
    # the others are unmodified.
    mode = os.stat(path).st_mode
    mode = mode & readExBits

    os.chmod(path, mode)
