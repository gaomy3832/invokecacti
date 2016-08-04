"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import re
import numpy as np
from collections import OrderedDict


# http://stackoverflow.com/a/385597
FLOAT_REGEX = r'[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'

INT_REGEX = r'[+-]? *\d+'


_RESULT_KEY2PATTERN = OrderedDict([
    ('latency', ('Access time \(ns\)\s*:\s*({})'\
            .format(FLOAT_REGEX), \
            lambda x: float(x) * 1e-9)),
    ('eread', ('Total dynamic read energy per access \(nJ\)\s*:\s*({})'\
            .format(FLOAT_REGEX), \
            lambda x: float(x) * 1e-9)),
    ('ewrite', ('Total dynamic write energy per access \(nJ\)\s*:\s*({})'\
            .format(FLOAT_REGEX), \
            lambda x: float(x) * 1e-9)),
    ('leakage', ('Total leakage power of a bank .* \(mW\)\s*:\s*({})'\
            .format(FLOAT_REGEX), \
            lambda x: float(x) * 1e-9)),
    ('height', ('Cache height x width \(mm\)\s*:\s*({0})\s*x\s*{0}'\
            .format(FLOAT_REGEX), \
            lambda x: float(x) * 1e-3)),
    ('width', ('Cache height x width \(mm\)\s*:\s*{0}\s*x\s*({0})'\
            .format(FLOAT_REGEX), \
            lambda x: float(x) * 1e-3)),
    ('area', ('Cache height x width \(mm\)\s*:\s*({0}\s*x\s*{0})'\
            .format(FLOAT_REGEX), \
            lambda x: np.prod([float(xx)*1e-3 for xx in x.split('x')]))),
    ])


def _extract_one(pattern, string, kvmap, keys, typefunc=lambda x:x):
    matches = re.findall(pattern, string, re.M)
    assert len(matches) == 1
    match = matches[0]
    if isinstance(match, tuple):
        assert len(match) == len(keys)
    else:
        assert len(keys) == 1
        match = (match,)
    for k, v in zip(keys, match):
        kvmap[k] = typefunc(v)


def parse(string):
    results = OrderedDict()
    for key, pattern in _RESULT_KEY2PATTERN.iteritems():
        _extract_one(pattern[0], string, results,
                [key], pattern[1])
    return results


