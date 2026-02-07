# -*- coding: utf-8 -*-

from collections import OrderedDict


class ReadOnlyOrderedDict(OrderedDict):
    """Read-only ordered dictionary.

    This was created since:
    - frozendict was rejected as PEP 416 (but is available as a package)
    - MappingProxyType (read-only proxy, not immutable per se) is
      similar to immutable frozendict, but is not available in Python 2.

    based on https://stackoverflow.com/a/19023331/4541104
    """

    # "$" and "%" are *mixed intentionally* since the blnk file may have
    #   come from another OS:

    def __init__(self):
        OrderedDict.__init__(self)
        self.__readonly = False

    def readonly(self, readonly=True):
        """Allow or deny modifying dictionary"""
        if readonly is None:
            readonly = False
        elif readonly not in (True, False):
            raise TypeError("readonly should be True or False (got %s)"
                            % (readonly))
        self.__readonly = readonly

    def __setitem__(self, key, value):
        if self.__readonly:
            raise TypeError("__setitem__ is not supported")
        return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        if self.__readonly:
            raise TypeError("__delitem__ is not supported")
        return dict.__delitem__(self, key)
