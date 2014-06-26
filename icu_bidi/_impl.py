#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 by science+computing ag
# Author: Anselm Kruis <a.kruis@science-computing.de>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

from __future__ import absolute_import, print_function, division

import ctypes.util
import threading
import weakref
import warnings
import array

from enum import IntEnum
import icu

__all__ = ['Bidi', 'UBiDiReorderingMode', 'UBiDiReorderingOption', 'UBiDiDirection', 'UBidiWriteReorderedOpt', 'UBiDiLevel']

class IcuBindingGenerator(object):
    TESTED_VERSIONS = ('53')
    NAME = 'icuuc'
    
    IN = 1
    OUT = 2
    INOUT = 3
    ZERO = 4
    
    def __init__(self, version):
        version = version.split('.')[0]
        libname = self.NAME
        try:
            lib = getattr(ctypes.cdll, libname + version)
        except AttributeError:
            libname = ctypes.util.find_library(libname)
            if libname is None:
                raise
            lib = getattr(ctypes.cdll, libname)
        if version not in self.TESTED_VERSIONS:
            warnings.warn("Version {} of library {} is untested.".format(version, lib._name))
        if array.array('u').itemsize != ctypes.sizeof(ctypes.c_wchar):
            # Completely untested.
            warnings.warn("Sizeof(Py_UNICODE) == {}, sizeof(wchar_t) =0 {}. Trouble ahead!!".format(array.array('u').itemsize, ctypes.sizeof(ctypes.c_wchar)))
        self.lib = lib
        self.version = version
        
    def function(self, name, restype=None, errcheck=None, *argspecs):
        if isinstance(errcheck, tuple):
            argspecs = (errcheck,) + argspecs
            errcheck = None
            
        argtypes = tuple(s[0] for s in argspecs)
        paramflags = tuple(s[1:] for s in argspecs)
        # prototype = ctypes.CFUNCTYPE(restype, *argtypes)
        # func = prototype((name + "_" + self.version, self.lib), paramflags)
        func = getattr(self.lib, name + "_" + self.version)
        func.argtypes = argtypes
        func.restype = restype
        if errcheck is not None:
            func.errcheck = errcheck
        return func

class ctypes_UBiDi(ctypes.Structure):
    pass

ctypes_P_UBiDi = ctypes.POINTER(ctypes_UBiDi)
ctypes_UBool = ctypes.c_int8
ctypes_UBiDiLevel = ctypes.c_uint8
ctypes_P_UBiDiLevel = ctypes.POINTER(ctypes_UBiDiLevel)
ctypes_UErrorCode = ctypes.c_int
ctypes_P_UErrorCode = ctypes.POINTER(ctypes_UErrorCode)
ctypes_P_c_int32 = ctypes.POINTER(ctypes.c_int32)

ctypes_P_UChar = ctypes.c_wchar_p  # at least for windows

class IcuErrChecker(object):
    DEFAULT_CHECKER = None  # to be overridden later
    def __init__(self):
        self.u_error_code = ctypes_UErrorCode(self.U_ZERO_ERROR)

    def _get_checker(self):
        return self

    @property
    def _as_parameter_(self):
        u_error_code = self._get_checker().u_error_code
        u_error_code.value = 0
        return ctypes.byref(u_error_code)
    
    @property
    def value(self):
        return self._get_checker().u_error_code.value

       
    @classmethod
    def errcheck(cls, result, func, arguments):
        for arg in arguments:
            if not isinstance(arg, cls):
                continue
            if arg.is_failure():
                v = arg.value
                raise icu.ICUError(v, icu.ICUError.messages.get(v, "Unknown error code "+str(v)))
            return arguments
        return arguments

    U_ZERO_ERROR = 0

    def is_failure(self):
        return self.value > self.U_ZERO_ERROR
    
    def is_success(self):
        return self.value <= self.U_ZERO_ERROR

class _DefaultIcuErrChecker(IcuErrChecker):
    repository = threading.local()
    
    def _get_checker(self):
        repository = self.repository
        try:
            checker = repository.checker
        except AttributeError:
            checker = IcuErrChecker()
            repository.checker = checker
        return checker
    
IcuErrChecker.DEFAULT_CHECKER = _DefaultIcuErrChecker()

class UBiDiLevel(IntEnum):
    UBIDI_LTR = 0
    """Paragraph level setting: LRT text
    """
    UBIDI_RTL = 1
    """Paragraph level setting: RTL text
    """
    UBIDI_DEFAULT_LTR = 0xfe
    """Paragraph level setting.

    Constant indicating that the base direction depends on the first strong directional character in the text according to the Unicode Bidirectional Algorithm. If no strong directional character is present, then set the paragraph level to 0 (left-to-right).

    If this value is used in conjunction with reordering modes UBIDI_REORDER_INVERSE_LIKE_DIRECT or UBIDI_REORDER_INVERSE_FOR_NUMBERS_SPECIAL, the text to reorder is assumed to be visual LTR, and the text after reordering is required to be the corresponding logical string with appropriate contextual direction. The direction of the result string will be RTL if either the righmost or leftmost strong character of the source text is RTL or Arabic Letter, the direction will be LTR otherwise.

    If reordering option UBIDI_OPTION_INSERT_MARKS is set, an RLM may be added at the beginning of the result string to ensure round trip (that the result string, when reordered back to visual, will produce the original source text).

    See Also
        UBIDI_REORDER_INVERSE_LIKE_DIRECT 
        UBIDI_REORDER_INVERSE_FOR_NUMBERS_SPECIAL 
    """
    UBIDI_DEFAULT_RTL = 0xff
    """Paragraph level setting.

    Constant indicating that the base direction depends on the first strong directional character in the text according to the Unicode Bidirectional Algorithm. If no strong directional character is present, then set the paragraph level to 1 (right-to-left).

    If this value is used in conjunction with reordering modes UBIDI_REORDER_INVERSE_LIKE_DIRECT or UBIDI_REORDER_INVERSE_FOR_NUMBERS_SPECIAL, the text to reorder is assumed to be visual LTR, and the text after reordering is required to be the corresponding logical string with appropriate contextual direction. The direction of the result string will be RTL if either the righmost or leftmost strong character of the source text is RTL or Arabic Letter, or if the text contains no strong character; the direction will be LTR otherwise.

    If reordering option UBIDI_OPTION_INSERT_MARKS is set, an RLM may be added at the beginning of the result string to ensure round trip (that the result string, when reordered back to visual, will produce the original source text).

    See Also
        UBIDI_REORDER_INVERSE_LIKE_DIRECT 
        UBIDI_REORDER_INVERSE_FOR_NUMBERS_SPECIAL 
    """
    UBIDI_MAX_EXPLICIT_LEVEL = 125
    """Maximum explicit embedding level.

    (The maximum resolved level can be up to UBIDI_MAX_EXPLICIT_LEVEL+1).
    """

class UBiDiReorderingMode(IntEnum):
    UBIDI_REORDER_DEFAULT = 0     
    """Regular Logical to Visual Bidi algorithm according to Unicode."""
    UBIDI_REORDER_NUMBERS_SPECIAL = 1
    """Logical to Visual algorithm which handles numbers in a way which mimicks the behavior of Windows XP."""
    UBIDI_REORDER_GROUP_NUMBERS_WITH_R = 2
    """Logical to Visual algorithm grouping numbers with adjacent R characters (reversible algorithm)."""
    UBIDI_REORDER_RUNS_ONLY = 3
    """Reorder runs only to transform a Logical LTR string to the Logical RTL string with the same display, or vice-versa.

    If this mode is set together with option UBIDI_OPTION_INSERT_MARKS, some Bidi controls in the source text may be removed and other controls may be added to produce the minimum combination which has the required display.
    """
    UBIDI_REORDER_INVERSE_NUMBERS_AS_L = 4
    """Visual to Logical algorithm which handles numbers like L (same algorithm as selected by ubidi_setInverse(TRUE).

    See Also
        ubidi_setInverse
    """
    UBIDI_REORDER_INVERSE_LIKE_DIRECT = 5
    """Visual to Logical algorithm equivalent to the regular Logical to Visual algorithm."""
    UBIDI_REORDER_INVERSE_FOR_NUMBERS_SPECIAL = 6
    """Inverse Bidi (Visual to Logical) algorithm for the UBIDI_REORDER_NUMBERS_SPECIAL Bidi algorithm."""
    UBIDI_REORDER_COUNT = 7
    """Number of values for reordering mode."""

class UBiDiReorderingOption(IntEnum):
    UBIDI_OPTION_DEFAULT = 0
    """option value for ubidi_setReorderingOptions: disable all the options which can be set with this function

    See Also
        ubidi_setReorderingOptions
    """
    UBIDI_OPTION_INSERT_MARKS = 1
    """option bit for ubidi_setReorderingOptions: insert Bidi marks (LRM or RLM) when needed to ensure correct result of a reordering to a Logical order

    This option must be set or reset before calling ubidi_setPara.

    This option is significant only with reordering modes which generate a result with Logical order, specifically:

        UBIDI_REORDER_RUNS_ONLY
        UBIDI_REORDER_INVERSE_NUMBERS_AS_L
        UBIDI_REORDER_INVERSE_LIKE_DIRECT
        UBIDI_REORDER_INVERSE_FOR_NUMBERS_SPECIAL

    If this option is set in conjunction with reordering mode UBIDI_REORDER_INVERSE_NUMBERS_AS_L or with calling ubidi_setInverse(TRUE), it implies option UBIDI_INSERT_LRM_FOR_NUMERIC in calls to function ubidi_writeReordered().

    For other reordering modes, a minimum number of LRM or RLM characters will be added to the source text after reordering it so as to ensure round trip, i.e. when applying the inverse reordering mode on the resulting logical text with removal of Bidi marks (option UBIDI_OPTION_REMOVE_CONTROLS set before calling ubidi_setPara() or option UBIDI_REMOVE_BIDI_CONTROLS in ubidi_writeReordered), the result will be identical to the source text in the first transformation.

    This option will be ignored if specified together with option UBIDI_OPTION_REMOVE_CONTROLS. It inhibits option UBIDI_REMOVE_BIDI_CONTROLS in calls to function ubidi_writeReordered() and it implies option UBIDI_INSERT_LRM_FOR_NUMERIC in calls to function ubidi_writeReordered() if the reordering mode is UBIDI_REORDER_INVERSE_NUMBERS_AS_L.

    See Also
        ubidi_setReorderingMode 
        ubidi_setReorderingOptions 
    """
    UBIDI_OPTION_REMOVE_CONTROLS = 2
    """
    option bit for ubidi_setReorderingOptions: remove Bidi control characters

    This option must be set or reset before calling ubidi_setPara.

    This option nullifies option UBIDI_OPTION_INSERT_MARKS. It inhibits option UBIDI_INSERT_LRM_FOR_NUMERIC in calls to function ubidi_writeReordered() and it implies option UBIDI_REMOVE_BIDI_CONTROLS in calls to that function.

    See Also
        ubidi_setReorderingMode 
        ubidi_setReorderingOptions 
    """
    UBIDI_OPTION_STREAMING = 4
    """
    option bit for ubidi_setReorderingOptions: process the output as part of a stream to be continued

    This option must be set or reset before calling ubidi_setPara.

    This option specifies that the caller is interested in processing large text object in parts. The results of the successive calls are expected to be concatenated by the caller. Only the call for the last part will have this option bit off.

    When this option bit is on, ubidi_setPara() may process less than the full source text in order to truncate the text at a meaningful boundary. The caller should call ubidi_getProcessedLength() immediately after calling ubidi_setPara() in order to determine how much of the source text has been processed. Source text beyond that length should be resubmitted in following calls to ubidi_setPara. The processed length may be less than the length of the source text if a character preceding the last character of the source text constitutes a reasonable boundary (like a block separator) for text to be continued.
    If the last character of the source text constitutes a reasonable boundary, the whole text will be processed at once.
    If nowhere in the source text there exists such a reasonable boundary, the processed length will be zero.
    The caller should check for such an occurrence and do one of the following:

        submit a larger amount of text with a better chance to include a reasonable boundary.
        resubmit the same text after turning off option UBIDI_OPTION_STREAMING.

    In all cases, this option should be turned off before processing the last part of the text.

    When the UBIDI_OPTION_STREAMING option is used, it is recommended to call ubidi_orderParagraphsLTR() with argument orderParagraphsLTR set to TRUE before calling ubidi_setPara so that later paragraphs may be concatenated to previous paragraphs on the right.

    See Also
        ubidi_setReorderingMode 
        ubidi_setReorderingOptions 
        ubidi_getProcessedLength 
        ubidi_orderParagraphsLTR 
    """

class UBiDiDirection(IntEnum):
    UBIDI_LTR = 0
    """Left-to-right text.

    This is a 0 value.

        As return value for ubidi_getDirection(), it means that the source string contains no right-to-left characters, or that the source string is empty and the paragraph level is even.
        As return value for ubidi_getBaseDirection(), it means that the first strong character of the source string has a left-to-right direction.
    """
    UBIDI_RTL = 1
    """Right-to-left text.

    This is a 1 value.

        As return value for ubidi_getDirection(), it means that the source string contains no left-to-right characters, or that the source string is empty and the paragraph level is odd.
        As return value for ubidi_getBaseDirection(), it means that the first strong character of the source string has a right-to-left direction.
    """
    UBIDI_MIXED = 2
    """Mixed-directional text.

        As return value for ubidi_getDirection(), it means that the source string contains both left-to-right and right-to-left characters.
    """
    UBIDI_NEUTRAL = 3
    """No strongly directional text.

        As return value for ubidi_getBaseDirection(), it means that the source string is missing or empty, or contains neither left-to-right nor right-to-left characters.
    """
    
class UBidiWriteReorderedOpt(IntEnum):
    UBIDI_KEEP_BASE_COMBINING = 1
    """option bit for ubidi_writeReordered(): keep combining characters after their base characters in RTL runs

    See Also
        ubidi_writeReordered
    """ 
    UBIDI_DO_MIRRORING = 2
    """option bit for ubidi_writeReordered(): replace characters with the "mirrored" property in RTL runs by their mirror-image mappings

    See Also
        ubidi_writeReordered
    """
    UBIDI_INSERT_LRM_FOR_NUMERIC = 4
    """option bit for ubidi_writeReordered(): surround the run with LRMs if necessary; this is part of the approximate "inverse Bidi" algorithm

    This option does not imply corresponding adjustment of the index mappings.

    See Also
        ubidi_setInverse 
        ubidi_writeReordered 
    """
    UBIDI_REMOVE_BIDI_CONTROLS = 8
    """option bit for ubidi_writeReordered(): remove Bidi control characters (this does not affect UBIDI_INSERT_LRM_FOR_NUMERIC)

    This option does not imply corresponding adjustment of the index mappings.

    See Also
        ubidi_writeReordered
    """ 
    UBIDI_OUTPUT_REVERSE = 16
    """option bit for ubidi_writeReordered(): write the output in reverse order

    This has the same effect as calling ubidi_writeReordered() first without this option, and then calling ubidi_writeReverse() without mirroring. Doing this in the same step is faster and avoids a temporary buffer. An example for using this option is output to a character terminal that is designed for RTL scripts and stores text in reverse order.

    See Also
        ubidi_writeReordered
    """

_bg = IcuBindingGenerator(icu.ICU_VERSION)

_pBiDi = (ctypes_P_UBiDi, _bg.IN, 'pBiDi')
_pErrorCode = (ctypes_P_UErrorCode, _bg.OUT, 'pErrorCode', IcuErrChecker.DEFAULT_CHECKER)

ubidi_open = _bg.function('ubidi_open', ctypes_P_UBiDi)
ubidi_close = _bg.function('ubidi_close', None, _pBiDi)
ubidi_setInverse = _bg.function('ubidi_setInverse', None, _pBiDi, (ctypes_UBool, _bg.IN, 'isInverse'))
ubidi_isInverse = _bg.function('ubidi_isInverse', ctypes_UBool, _pBiDi)
ubidi_setReorderingMode = _bg.function('ubidi_setReorderingMode', None, _pBiDi, (ctypes.c_int, _bg.IN, 'reorderingMode'))
ubidi_getReorderingMode = _bg.function('ubidi_getReorderingMode', ctypes.c_int, _pBiDi)
ubidi_setReorderingOptions = _bg.function('ubidi_setReorderingOptions', None, _pBiDi, (ctypes.c_uint32, _bg.IN, 'reorderingOptions'))
ubidi_getReorderingOptions = _bg.function('ubidi_getReorderingOptions', ctypes.c_uint32, _pBiDi)
ubidi_setPara = _bg.function('ubidi_setPara', None, IcuErrChecker.errcheck, 
                             _pBiDi, 
                             (ctypes_P_UChar, _bg.IN, 'text'), 
                             (ctypes.c_int32, _bg.IN, 'length', -1),
                             (ctypes_UBiDiLevel, _bg.IN, 'paraLevel', UBiDiLevel.UBIDI_LTR),
                             (ctypes_P_UBiDiLevel, _bg.IN, 'embeddingLevels', ctypes_P_UBiDiLevel()),
                             _pErrorCode)
ubidi_getLength = _bg.function('ubidi_getLength', ctypes.c_int32, _pBiDi)
ubidi_countRuns = _bg.function('ubidi_countRuns', ctypes.c_int32, IcuErrChecker.errcheck, _pBiDi, _pErrorCode)
ubidi_getProcessedLength = _bg.function('ubidi_getProcessedLength', ctypes.c_int32, _pBiDi)
ubidi_getResultLength = _bg.function('ubidi_getResultLength', ctypes.c_int32, _pBiDi)

ubidi_writeReordered = _bg.function('ubidi_writeReordered', ctypes.c_int32, IcuErrChecker.errcheck,
                                    _pBiDi,
                                    (ctypes_P_UChar, _bg.OUT, 'dest'),  
                                    (ctypes.c_int32, _bg.IN, 'destSize'),
                                    (ctypes.c_uint16, _bg.IN, 'options', 0),
                                    _pErrorCode)
ubidi_getVisualRun = _bg.function('ubidi_getVisualRun', ctypes.c_int, 
                                  _pBiDi, 
                                  (ctypes.c_int32, _bg.IN, 'runIndex'),
                                  (ctypes_P_c_int32, _bg.OUT, 'pLogicalStart'),
                                  (ctypes_P_c_int32, _bg.OUT, 'pLength'))
ubidi_getLogicalMap = _bg.function('ubidi_getLogicalMap', None, IcuErrChecker.errcheck,
                                   _pBiDi,
                                   (ctypes_P_c_int32, _bg.OUT, 'indexMap'),
                                   _pErrorCode)


class Bidi(object):
    _all_bidi_objects = {}
    
    def __init__(self):
        self.pbidi = ubidi_open()
        addr = ctypes.addressof(self.pbidi.contents)
        wr = weakref.ref(self.pbidi, self.__on_bidi_delete)
        self._all_bidi_objects[id(wr)] = (addr, wr)
        
    @classmethod
    def __on_bidi_delete(cls, wref):
        try:
            addr = cls._all_bidi_objects.pop(id(wref))[0]
            ubidi_close(ctypes_P_UBiDi(ctypes_UBiDi.from_address(addr)))
        except Exception:
            pass

    @property
    def inverse(self):
        return ubidi_isInverse(self.pbidi)

    @inverse.setter
    def inverse(self, isInverse):
        ubidi_setInverse(self.pbidi, bool(isInverse))
        
    @property
    def reordering_mode(self):
        return ubidi_getReorderingMode(self.pbidi)

    @reordering_mode.setter
    def reordering_mode(self, reorderingMode):
        ubidi_setReorderingMode(self.pbidi, reorderingMode)

    @property
    def reordering_options(self):
        return ubidi_getReorderingOptions(self.pbidi)

    @reordering_options.setter
    def reordering_options(self, reorderingOptions):
        ubidi_setReorderingOptions(self.pbidi, reorderingOptions)

    @property
    def length(self):
        return ubidi_getLength(self.pbidi)
    
    @property
    def processed_length(self):
        return ubidi_getProcessedLength(self.pbidi)
    
    @property
    def result_length(self):
        return ubidi_getResultLength(self.pbidi)
    
    def set_para(self, text, paraLevel=UBiDiLevel.UBIDI_LTR, embeddingLevels=None):
        if not isinstance(text, unicode):
            text = unicode(text)
        length = len(text)
        ubidi_setPara(self.pbidi, text, length, paraLevel, embeddingLevels, IcuErrChecker.DEFAULT_CHECKER)
        
    def count_runs(self):
        return ubidi_countRuns(self.pbidi, IcuErrChecker.DEFAULT_CHECKER)

    def get_reordered(self, options):
        n_runs = self.count_runs()
        maxsize = self.length + 2*n_runs
        buf = ctypes.create_unicode_buffer(maxsize)
        buf_len = ubidi_writeReordered(self.pbidi, buf, maxsize, int(options), IcuErrChecker.DEFAULT_CHECKER)
        return buf[:buf_len]

    def get_visual_run(self, runIndex):
        start = ctypes.c_int32()
        length = ctypes.c_int32()
        direction = ubidi_getVisualRun(self.pbidi, int(runIndex), ctypes.byref(start), ctypes.byref(length))
        return direction, start.value, length.value
