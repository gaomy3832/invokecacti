"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import invokecacti

cacti_exe='/armadillo/users/mgao12/research/tools/mcpat/mcpat/cacti/cacti'

cacti = invokecacti.InvokeCACTIP('.', cacti_exe=cacti_exe)

cacti.invoke(size=65536, assoc=4, line=64)



