"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import invokecacti

cacti_exe='/armadillo/users/mgao12/research/tools/mcpat/mcpat/cacti/cacti'

cacti = invokecacti.Invoke('.', cacti_exe=cacti_exe)

cacti.invoke(65536, 4, 64)



