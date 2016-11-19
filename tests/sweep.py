"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

from collections import OrderedDict
import json

import invokecacti

cacti_exe='/armadillo/users/mgao12/research/tools/mcpat/mcpat/cacti/cacti'

cacti = invokecacti.Invoke('output',
        cfg_dir='output/cfgs', log_dir='output/logs', cacti_exe=cacti_exe)

cfgs = OrderedDict()

for size in [ 2**i for i in range(15, 24+1) ]:
    if size >= 1024*1024:
        cell_array_type='lstp'
    else:
        cell_array_type='hp'

    cfgs[size] = cacti.invoke(size, 8, 64, tech=0.045, memtype='cache',
            dcell=cell_array_type, tcell=cell_array_type)


with open('out.json', 'w') as fh:
    json.dump(cfgs, fh, indent=2)
    fh.write('\n')

