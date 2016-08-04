"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import os
from string import Template


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_cfg(cfgDict, filename=None):
    '''
    Generate the cfg file for CACTI.

    Return the cfg file content. If `filename` is not None, also create the cfg
    file.
    '''

    # load template file.

    tmplfilename = os.path.join(_THIS_DIR, 'cache.cfg.template')
    if not os.path.isfile(tmplfilename):
        raise IOError(tmplfilename)

    with open(tmplfilename, 'r') as tfile:
        tmpl = Template(tfile.read())

    # check config dict.

    for key in ['size', 'assoc', 'line', 'banks', 'tech', 'temp', 'level',
            'type', 'rwports', 'rdports', 'wrports',
            'dcell', 'dperi', 'tcell', 'tperi']:
        if key not in cfgDict:
            raise KeyError(key)

    memtype = cfgDict['type']
    if memtype != 'cache' and memtype != 'ram' and memtype != 'cam' \
            and memtype != 'main memory':
        raise ValueError(memtype)

    for key in ['dcell', 'dperi', 'tcell', 'tperi']:
        array_type = cfgDict[key]
        if array_type != 'itrs-hp' and array_type != 'itrs-lstp' \
                and array_type != 'itrs-lop' and array_type != 'lp-dram' \
                and array_type != 'comm-dram':
            raise ValueError(array_type)

    # fill template.

    content = tmpl.substitute(SIZE=cfgDict['size'], WAYS=cfgDict['assoc'],
            BANKS=cfgDict['banks'], LINE=cfgDict['line'],
            TECHNODE=cfgDict['tech'], TEMP=cfgDict['temp'],
            LEVEL=cfgDict['level'], TYPE=cfgDict['type'],
            RWPORT=cfgDict['rwports'], RDPORT=cfgDict['rdports'],
            WRPORT=cfgDict['wrports'], DARRAY_CELL_TYPE=cfgDict['dcell'],
            DARRAY_PERI_TYPE=cfgDict['dperi'],
            TARRAY_CELL_TYPE=cfgDict['tcell'],
            TARRAY_PERI_TYPE=cfgDict['tperi'],
            # dependent vars
            IOWIDTH=8*cfgDict['line'])

    if filename is not None:
        with open(filename, 'w') as fh:
            fh.write(content)

    return content

