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

from icu_bidi import _impl as I
import ctypes
import unittest
import icu

visual = u"Latin1 \u060c(\u0643 567 \u062a\u0643\u0631\u0634> More latin 123 \u0643\u062a"
#          01234567     89     012345     6     7     8     901234567890123456     7     8
#          0                   1                             2         3

logical_ltr = u"Latin1 \u060c(\u0634\u0631\u0643\u062a 567 \u0643> More latin 123 \u062a\u0643"
logical_rtl = u"\u062a\u0643 123 More latin <\u0634\u0631\u0643\u062a 567 \u0643)\u060c Latin1"
runs_rtl = [(1, 35, 3), (0, 32, 3), (1, 31, 1), (0, 21, 10), (1, 14, 7), (0, 11, 3), (1, 6, 5), (0, 0, 5), (0, 5, 1)]


class TestBidi(unittest.TestCase):
    def testInverseBidi(self):
        bidi = I.Bidi()
        bidi.inverse = True
        self.assertTrue(bidi.inverse)

        bidi.reordering_mode = I.UBiDiReorderingMode.UBIDI_REORDER_INVERSE_LIKE_DIRECT
        bidi.reordering_options = I.UBiDiReorderingOption.UBIDI_OPTION_INSERT_MARKS

        self.assertFalse(bidi.inverse)
        self.assertEquals(bidi.reordering_mode, I.UBiDiReorderingMode.UBIDI_REORDER_INVERSE_LIKE_DIRECT)
        self.assertEquals(bidi.reordering_options, I.UBiDiReorderingOption.UBIDI_OPTION_INSERT_MARKS)

        bidi.set_para(visual, I.UBiDiLevel.UBIDI_RTL, None)
        length = bidi.length
        self.assertEquals(length, len(visual))

        res = bidi.get_reordered(0
                                 | I.UBidiWriteReorderedOpt.UBIDI_DO_MIRRORING
                                 | I.UBidiWriteReorderedOpt.UBIDI_KEEP_BASE_COMBINING
                                 #| UBidiWriteReorderedOpt.UBIDI_INSERT_LRM_FOR_NUMERIC
                                 )
        n_runs = bidi.count_runs()
        runs = [bidi.get_visual_run(i) for i in range(n_runs)]
        bidi = None

        r_sum = sum(r[2] for r in runs)
        self.assertListEqual(runs, runs_rtl)
        self.assertEqual(n_runs, len(runs_rtl))
        self.assertEqual(length, r_sum)
        self.assertEqual(res, logical_rtl)


class TestBinding(unittest.TestCase):
    def testInverseBidi(self):
        pBiDi = I.ubidi_open()
        self.addCleanup(I.ubidi_close, pBiDi)

        I.ubidi_setInverse(pBiDi, True)
        self.assertTrue(I.ubidi_isInverse(pBiDi))

        I.ubidi_setReorderingMode(pBiDi, I.UBiDiReorderingMode.UBIDI_REORDER_INVERSE_LIKE_DIRECT)
        I.ubidi_setReorderingOptions(pBiDi, I.UBiDiReorderingOption.UBIDI_OPTION_INSERT_MARKS)

        self.assertFalse(I.ubidi_isInverse(pBiDi))
        self.assertEquals(I.ubidi_getReorderingMode(pBiDi), I.UBiDiReorderingMode.UBIDI_REORDER_INVERSE_LIKE_DIRECT)
        self.assertEquals(I.ubidi_getReorderingOptions(pBiDi), I.UBiDiReorderingOption.UBIDI_OPTION_INSERT_MARKS)

        I.ubidi_setPara(pBiDi, visual, len(visual), I.UBiDiLevel.UBIDI_RTL, None, I.IcuErrChecker.DEFAULT_CHECKER)
        length = I.ubidi_getLength(pBiDi)
        self.assertEquals(length, len(visual))

        n_runs = I.ubidi_countRuns(pBiDi, I.IcuErrChecker.DEFAULT_CHECKER)
        size = length + 2 * n_runs
        buf = ctypes.create_unicode_buffer(size)
        buf_len = I.ubidi_writeReordered(pBiDi, buf, size,
                                         I.UBidiWriteReorderedOpt.UBIDI_DO_MIRRORING |
                                         I.UBidiWriteReorderedOpt.UBIDI_KEEP_BASE_COMBINING |
                                         # UBidiWriteReorderedOpt.UBIDI_INSERT_LRM_FOR_NUMERIC |
                                         0, I.IcuErrChecker.DEFAULT_CHECKER)
        r_sum = 0
        runs = []
        for i in range(n_runs):
            r_start = ctypes.c_int32()
            r_length = ctypes.c_int32()
            direction = I.ubidi_getVisualRun(pBiDi, i, ctypes.byref(r_start), ctypes.byref(r_length))
            r_sum += r_length.value
            runs.append((direction, r_start.value, r_length.value))
            # print("Run", i, "direction", direction, "start", r_start.value, "length", r_length.value)
        res = buf[:buf_len]
        self.assertListEqual(runs, runs_rtl)
        self.assertEqual(n_runs, len(runs_rtl))
        self.assertEqual(length, r_sum)

        #print("Result  :", repr(res))
        #print("Expected:", repr(logical_rtl))
        self.assertEqual(res, logical_rtl)

    def testErrorChecker(self):
        pBiDi = I.ubidi_open()
        self.addCleanup(I.ubidi_close, pBiDi)
        self.assertRaises(icu.ICUError, I.ubidi_writeReordered, pBiDi, None, -1, 0, I.IcuErrChecker.DEFAULT_CHECKER)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
