"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import os
from string import Template


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_cfg(cfg_dict, filename=None):
    '''
    Generate the cfg file for CACTI.

    Return the cfg file content. If `filename` is not None, also create the cfg
    file.
    '''

    # load template file.

    tmplfilename = os.path.join(_THIS_DIR,
                                'cfg_templates',
                                'cacti-p.cfg.template')
    if not os.path.isfile(tmplfilename):
        raise IOError(tmplfilename)

    with open(tmplfilename, 'r') as tfile:
        tmpl = Template(tfile.read())

    # check config dict.

    for key in ['size', 'assoc', 'line', 'banks', 'tech', 'temp', 'level',
                'type', 'rwports', 'rdports', 'wrports',
                'dcell', 'dperi', 'tcell', 'tperi']:
        if key not in cfg_dict:
            raise KeyError(key)

    memtype = cfg_dict['type']
    if memtype != 'cache' and memtype != 'ram' and memtype != 'cam' \
            and memtype != 'main memory':
        raise ValueError(memtype)

    for key in ['dcell', 'dperi', 'tcell', 'tperi']:
        array_type = cfg_dict[key]
        if array_type != 'itrs-hp' and array_type != 'itrs-lstp' \
                and array_type != 'itrs-lop' and array_type != 'lp-dram' \
                and array_type != 'comm-dram':
            raise ValueError(array_type)

    # fill template.

    content = tmpl.substitute(SIZE=cfg_dict['size'], WAYS=cfg_dict['assoc'],
                              BANKS=cfg_dict['banks'], LINE=cfg_dict['line'],
                              TECHNODE=cfg_dict['tech'], TEMP=cfg_dict['temp'],
                              LEVEL=cfg_dict['level'], TYPE=cfg_dict['type'],
                              RWPORT=cfg_dict['rwports'],
                              RDPORT=cfg_dict['rdports'],
                              WRPORT=cfg_dict['wrports'],
                              DARRAY_CELL_TYPE=cfg_dict['dcell'],
                              DARRAY_PERI_TYPE=cfg_dict['dperi'],
                              TARRAY_CELL_TYPE=cfg_dict['tcell'],
                              TARRAY_PERI_TYPE=cfg_dict['tperi'],
                              # dependent vars
                              IOWIDTH=8*cfg_dict['line'])

    if filename is not None:
        with open(filename, 'w') as fh:
            fh.write(content)

    return content

