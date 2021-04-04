"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import re
from collections import OrderedDict
import numpy as np


# http://stackoverflow.com/a/385597
FLOAT_REGEX = r'[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'

INT_REGEX = r'[+-]? *\d+'


class ResultPattern():
    ''' Pattern of a result that needs to be extracted. '''

    def __init__(self, pattern, keys, funcs):
        self.regex = re.compile(pattern, re.M)
        if not isinstance(keys, (list, tuple)):
            self.keys = [keys]
        else:
            self.keys = keys
        if not isinstance(funcs, (list, tuple)):
            self.funcs = [funcs]
        else:
            self.funcs = funcs

        if self.regex.groups < 1:
            raise ValueError('{}: pattern is invalid regex pattern; '
                             'at least one group must be given.'
                             .format(self.__class__.__name__))
        if len(self.keys) != len(self.funcs):
            raise ValueError('{}: keys have unmatched length with functions.'
                             .format(self.__class__.__name__))

        if len(self.keys) != self.regex.groups and len(self.keys) != 1:
            raise ValueError('{}: pattern should either have the matching '
                             'length with keys, or be reduced to a single '
                             'key.'.format(self.__class__.__name__))

    def result_keys(self):
        '''
        Return keys of the result.
        '''
        return self.keys

    def extract(self, string):
        '''
        Extract result from given string.
        '''
        matches = self.regex.findall(string)
        if len(matches) != 1:
            raise RuntimeError('{}: fail to extract result.'
                               .format(self.__class__.__name__))
        match = matches[0]
        if not isinstance(match, tuple):
            match = (match,)
        if len(self.funcs) == len(match):
            values = [f(v) for f, v in zip(self.funcs, match)]
        else:
            values = [self.funcs[0](*match)]
        assert len(values) == len(self.keys)
        return OrderedDict(zip(self.keys, values))


class ResultParser():
    ''' CACTI output parser. '''

    def __init__(self):
        self.result_patterns = []
        self._add_patterns()

    def version_name(self):
        '''
        Return the corresponding CACTI version name.
        '''
        raise NotImplementedError('{}: version_name() not implemented.'
                                  .format(self.__class__.__name__))

    def parse(self, string):
        '''
        Parse the given string and return an ordered dict of the results.
        '''
        results = OrderedDict()
        for rp in self.result_patterns:
            results.update(rp.extract(string))
        return results

    def _add_patterns(self):
        '''
        Add patterns to be parsed.
        '''

    @staticmethod
    def _milli(val):
        return float(val) * 1e-3

    @staticmethod
    def _nano(val):
        return float(val) * 1e-9


class ResultParserCACTIP(ResultParser):
    ''' CACTI-P output parser. '''

    def version_name(self):
        return 'CACTI-P'

    def _add_patterns(self):
        self.result_patterns += [
            ResultPattern(r'Access time \(ns\)\s*:\s*({})'.format(FLOAT_REGEX),
                          'latency',
                          ResultParser._nano),
            ResultPattern(r'Total dynamic read energy per access \(nJ\)\s*:\s*'
                          r'({})'.format(FLOAT_REGEX),
                          'eread',
                          ResultParser._nano),
            ResultPattern(r'Total dynamic write energy per access \(nJ\)\s*:\s*'
                          r'({})'.format(FLOAT_REGEX),
                          'ewrite',
                          ResultParser._nano),
            ResultPattern(r'(?ms)'
                          r'Number of banks\s*:\s*({})\s*'
                          r'.*'
                          r'Total leakage power of a bank .* \(mW\)\s*:\s*({})'
                          r'\s*Cache'.format(INT_REGEX, FLOAT_REGEX),
                          'leakage',
                          lambda x, y: int(x) * ResultParser._milli(y)),
            ResultPattern(r'Cache height x width \(mm\)\s*:\s*({0})\s*x\s*{0}'
                          .format(FLOAT_REGEX),
                          'height',
                          ResultParser._milli),
            ResultPattern(r'Cache height x width \(mm\)\s*:\s*{0}\s*x\s*({0})'
                          .format(FLOAT_REGEX),
                          'width',
                          ResultParser._milli),
            ResultPattern(r'Cache height x width \(mm\)\s*:\s*({0}\s*x\s*{0})'
                          .format(FLOAT_REGEX),
                          'area',
                          lambda x: np.prod([ResultParser._milli(xx)
                                             for xx in x.split('x')]))]


class ResultParserCACTI7(ResultParserCACTIP):
    ''' CACTI-7 output parser. '''

    # Based on CACTI-P.

    def version_name(self):
        return 'CACTI-7'

