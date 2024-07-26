# -*- coding: utf-8 -*-
"""Ways of dealing with macro-expanded code, e.g. caching or
re-serializing it."""

import importlib
import logging
import marshal
import os
import shutil

from . import unparse


logger = logging.getLogger(__name__)


def wr_long(f, x):
    """Internal; write a 32-bit int to a file in little-endian order."""
    f.write(chr( x        & 0xff))
    f.write(chr((x >> 8)  & 0xff))
    f.write(chr((x >> 16) & 0xff))
    f.write(chr((x >> 24) & 0xff))


class NullExporter(object):
    def export_transformed(self, code, tree, module_name, file_name):
        pass

    def find(self, file_path, pathname, description, module_name,
             package_path):
        pass


class SaveExporter(object):
    def __init__(self, directory="exported", root=os.getcwd()):
        self.root = os.path.abspath(root)
        self.directory = os.path.abspath(directory)
        shutil.rmtree(self.directory, ignore_errors=True)
        shutil.copytree(self.root, directory)

    def export_transformed(self, code, tree, module_name, file_name):

        # do the export only if module's file_name is a subpath of the
        # root
        logger.debug('Asked to export module %r', file_name)
        if os.path.commonprefix([self.root, file_name]) == self.root:

            new_path = os.path.join(
                self.directory,
                os.path.relpath(file_name, self.root)
            )

            with open(new_path, "w") as f:
                f.write(unparse(tree))
            logger.debug('Exported module %r to %r', file_name, new_path)

    def find(self, file_path, pathname, description, module_name, package_path):
        pass


suffix = __debug__ and 'c' or 'o'


import importlib.util

def load_compiled_module(name, pathname, file=None):
    spec = importlib.util.spec_from_file_location(name, pathname, loader=None, submodule_search_locations=None)
    module = importlib.util.module_from_spec(spec)

    if file:
        # If the file is provided, set __file__ attribute in the module
        setattr(module, "__file__", file.name)

    spec.loader.exec_module(module)

    return module


class PycExporter(object):
    def __init__(self, root=os.getcwd()):
        self.root = root

    def export_transformed(self, code, tree, module_name, file_name):
        """TODO: this needs to be updated, look into py_compile.compile, the
        following code was copied verbatim from there on python2"""
        f = open(file_name + suffix , 'wb')
        f.write('\0\0\0\0')
        timestamp = long(os.fstat(f.fileno()).st_mtime)
        wr_long(f, timestamp)
        marshal.dump(code, f)
        f.flush()
        f.seek(0, 0)
        f.write(importlib.util.MAGIC_NUMBER))

    def find(self, file_path, pathname, description, module_name, package_path):
        try:
            file = open(file_path, 'rb')
            f = open(file.name + suffix, 'rb')
            py_time = os.fstat(file.fileno()).st_mtime
            pyc_time = os.fstat(f.fileno()).st_mtime

            if py_time > pyc_time:
                return None
            x = load_compiled_module(module_name, pathname + suffix, f)
            return x
        except Exception as e:
            # print(e)
            raise
