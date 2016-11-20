"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import sys
import os
import tempfile
import subprocess
import json
import errno
from collections import OrderedDict

from .config import ConfigCACTIP
from .result_parser import ResultParserCACTIP


# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class Invoke(object):
    '''
    Environment class to invoke CACTI.
    '''

    def __init__(self, output_dir, cfg_dir=None, log_dir=None, cacti_exe=None):
        '''
        `output_dir` stores the json files for the results.

        `cfg_dir` stores the CACTI input cfg files; `log_dir` stores the CACTI
        output log files.

        `cacti_exe` specifies the CACTI executable path. If missing, infer from
        env var `CACTIPATH`.
        '''

        self.output_dir = os.path.abspath(output_dir)
        self.cfg_dir = os.path.abspath(cfg_dir) if cfg_dir is not None else None
        self.log_dir = os.path.abspath(log_dir) if log_dir is not None else None

        if cacti_exe is None:
            try:
                cacti_exe = os.path.join(os.environ.get('CACTIPATH'), 'cacti')
            except KeyError as e:
                sys.stderr.write('CACTI path is not provided and cannot find '
                                 'env var CACTIPATH.\n')
                sys.stderr.flush()
                raise e

        if not os.path.isfile(cacti_exe) or not os.access(cacti_exe, os.X_OK):
            sys.stderr.write('CACTI path or env var CACTIPATH is invalid.\n')
            sys.stderr.flush()
            raise ValueError(cacti_exe)

        self.cacti_exe = os.path.abspath(cacti_exe)


    @staticmethod
    def _cfg_name_str(size, assoc, line, banks, tech, temp, level, memtype,
                      rwports, rdports, wrports, dcell, dperi, tcell, tperi):
        return 's{}_w{}_l{}_b{}_t{}_{}k_{}_{}_rw{}_rd{}_wr{}_{}_{}_{}_{}'\
                .format(size, assoc, line, banks, tech, temp, level, memtype,
                        rwports, rdports, wrports, dcell, dperi, tcell, tperi)


    @staticmethod
    def _format_array_type(array_type):
        if array_type == 'itrs-hp' or array_type == 'itrs-lstp' \
                or array_type == 'itrs-lop' or array_type == 'lp-dram' \
                or array_type == 'comm-dram':
            return array_type
        elif array_type == 'hp' or array_type == 'lstp' or array_type == 'lop':
            return 'itrs-' + array_type
        elif array_type == 'dram':
            return 'comm-dram'
        else:
            raise ValueError(array_type)


    def invoke(self, size, assoc, line, banks=1, tech=0.032, temp=350,
               level='L1', memtype='cache', rwports=0, rdports=1, wrports=1,
               dcell='hp', dperi='hp', tcell='hp', tperi='hp'):
        '''
        Invoke CACTI for the specific configuration.
        '''

        dcell = Invoke._format_array_type(dcell)
        dperi = Invoke._format_array_type(dperi)
        tcell = Invoke._format_array_type(tcell)
        tperi = Invoke._format_array_type(tperi)

        cfg_dict = OrderedDict()
        cfg_dict['SIZE'] = size
        cfg_dict['WAYS'] = assoc
        cfg_dict['LINE'] = line
        cfg_dict['BANKS'] = banks
        cfg_dict['TECHNODE'] = tech
        cfg_dict['TEMP'] = temp
        cfg_dict['LEVEL'] = level
        cfg_dict['TYPE'] = memtype
        cfg_dict['RWPORT'] = rwports
        cfg_dict['RDPORT'] = rdports
        cfg_dict['WRPORT'] = wrports
        cfg_dict['DARRAY_CELL_TYPE'] = dcell
        cfg_dict['DARRAY_PERI_TYPE'] = dperi
        cfg_dict['TARRAY_CELL_TYPE'] = tcell
        cfg_dict['TARRAY_PERI_TYPE'] = tperi
        # dependent vars.
        cfg_dict['IOWIDTH'] = 8 * line

        cfg = ConfigCACTIP(cfg_dict)

        name = Invoke._cfg_name_str(size, assoc, line, banks, tech, temp, level,
                                    memtype, rwports, rdports, wrports,
                                    dcell, dperi, tcell, tperi)

        # create cfg file.
        if self.cfg_dir is not None:
            _mkdir_p(self.cfg_dir)
            cfg_fname = os.path.join(self.cfg_dir, name + '.cfg')
            cfg.generate(cfg_fname)
        else:
            with tempfile.NamedTemporaryFile(suffix='.cfg', delete=False) \
                    as tempfh:
                tempfh.write(cfg.generate())
                cfg_fname = tempfh.name

        # run.
        try:
            with open(os.devnull, 'w') as fnull:
                outstr = subprocess.check_output( \
                        [self.cacti_exe, '-infile', cfg_fname],
                        stderr=fnull, cwd=tempfile.gettempdir())
        except subprocess.CalledProcessError as e:
            raise RuntimeError('CACTI exits with {}'.format(e.returncode))

        # remove temporary cfg file.
        if self.cfg_dir is None:
            os.remove(cfg_fname)

        # write log file.
        if self.log_dir is not None:
            _mkdir_p(self.log_dir)
            log_fname = os.path.join(self.log_dir, name + '.log')
            with open(log_fname, 'w') as fh:
                fh.write(outstr)

        # parse output.
        results = ResultParserCACTIP().parse(outstr)
        # update() loses order.
        for key, val in results.items():
            cfg_dict[key] = val

        # write output json file.
        _mkdir_p(self.output_dir)
        json_fname = os.path.join(self.output_dir, name + '.json')
        with open(json_fname, 'w') as fh:
            json.dump(cfg_dict, fh, indent=2)
            fh.write('\n')

        return cfg_dict


    def get_cacti_exe(self):
        '''
        Path to CACTI executable.
        '''
        return self.cacti_exe


    def get_output_dir(self):
        '''
        Output directory.
        '''
        return self.output_dir

