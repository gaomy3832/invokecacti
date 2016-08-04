"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import cacti_invoke

cacti_exe='/armadillo/users/mgao12/research/tools/mcpat/mcpat10/cacti/cacti'

cacti = cacti_invoke.Invoke('.', cacti_exe=cacti_exe)

cacti.invoke(65536, 4, 64)



