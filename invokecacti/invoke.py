"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import errno
import json
import os
import subprocess
from collections import OrderedDict
from tempfile import NamedTemporaryFile

from . import config
from . import result_parser


# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class Invoke():
    '''
    Environment class to invoke CACTI.
    '''

    def __init__(self, output_dir, cfg_dir=None, log_dir=None, cacti_path=None):
        '''
        `output_dir` stores the json files for the results.

        `cfg_dir` stores the CACTI input cfg files; `log_dir` stores the CACTI
        output log files.

        `cacti_path` specifies the CACTI directory path. If missing, infer from
        env var `CACTIPATH`.
        '''

        if cacti_path is None:
            cacti_path = os.environ.get('CACTIPATH', None)
            if not cacti_path:
                raise EnvironmentError('{}: CACTI path is not provided and '
                                       'cannot find env var CACTIPATH.'
                                       .format(self.__class__.__name__))
        cacti_exe = os.path.join(cacti_path, 'cacti')
        if not os.path.isfile(cacti_exe) or not os.access(cacti_exe, os.X_OK):
            raise ValueError('{}: CACTI exe {} is invalid.'
                             .format(self.__class__.__name__, cacti_exe))
        self.cacti_path = os.path.abspath(cacti_path)
        self.cacti_exe = os.path.abspath(cacti_exe)

        self.output_dir = os.path.abspath(output_dir)
        self.cfg_dir = os.path.abspath(cfg_dir) if cfg_dir is not None else None
        self.log_dir = os.path.abspath(log_dir) if log_dir is not None else None

        self.cfg_cls = config.Config
        self.res_cls = result_parser.ResultParser

    def get_cacti_exe(self):
        ''' Path to CACTI executable. '''
        return self.cacti_exe

    def get_output_dir(self):
        ''' Output directory. '''
        return self.output_dir

    def _get_arguments(self):
        '''
        Invoke arguments as a list of tuples.
        Each tuple is
        - key name in invoke() method
        - key name in template file
        - optional default value
        '''
        # pylint: disable=no-self-use
        return [('size', 'SIZE'),
                ('assoc', 'WAYS'),
                ('line', 'LINE'),
                ('banks', 'BANKS', 1),
                ('tech', 'TECHNODE', 0.032),
                ('temp', 'TEMP', 350),
                ('level', 'LEVEL', 'L1'),
                ('memtype', 'TYPE', 'cache'),
                ('rwports', 'RWPORT', 0),
                ('rdports', 'RDPORT', 1),
                ('wrports', 'WRPORT', 1),
                ('dcell', 'DARRAY_CELL_TYPE', 'hp'),
                ('dperi', 'DARRAY_PERI_TYPE', 'hp'),
                ('tcell', 'TARRAY_CELL_TYPE', 'hp'),
                ('tperi', 'TARRAY_PERI_TYPE', 'hp'),
               ]

    def invoke(self, **kwargs):
        '''
        Invoke CACTI for the specific configuration.
        '''

        return_dict = OrderedDict()

        # create config.
        param_dict = OrderedDict()
        try:
            for tpl in self._get_arguments():
                try:
                    arg, key = tpl[:2]
                except ValueError:
                    raise ValueError('{}: bad argument tuple {}.'
                                     .format(self.__class__.__name__, tpl)) from None
                if len(tpl) >= 3:
                    defval = tpl[2]
                    param_dict[key] = kwargs.pop(arg, defval)
                else:
                    param_dict[key] = kwargs.pop(arg)
        except KeyError as e:
            raise KeyError('{}: must provide argument {}.'
                           .format(self.__class__.__name__, str(e))) from e
        if len(kwargs) > 0:
            raise TypeError('{}: invalid argument(s) {}'
                            .format(self.__class__.__name__, str(kwargs.keys())))
        cfg = self.cfg_cls(param_dict)
        name = cfg.config_name()

        # write cfg file.
        if not isinstance(cfg, config.Config):
            raise RuntimeError('{}: _make_config() must return a Config class.'
                               .format(self.__class__.__name__))
        if self.cfg_dir is not None:
            _mkdir_p(self.cfg_dir)
            cfg_fname = os.path.join(self.cfg_dir, name + '.cfg')
            cfg.generate(cfg_fname)
        else:
            with NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as tempfh:
                tempfh.write(cfg.generate())
                cfg_fname = tempfh.name

        # run.
        try:
            with open(os.devnull, 'w') as fnull:
                outstr = subprocess.check_output(
                    [self.cacti_exe, '-infile', cfg_fname],
                    stderr=fnull, cwd=self.cacti_path, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError('{}: CACTI exits with {}'
                               .format(self.__class__.__name__, e.returncode)) from e

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
        results = self.res_cls().parse(outstr)

        # compose return dict.
        # update() loses order.
        for key, val in cfg.config_dict().items():
            return_dict[key.lower()] = val
        for key, val in results.items():
            return_dict[key.lower()] = val

        # write output json file.
        _mkdir_p(self.output_dir)
        json_fname = os.path.join(self.output_dir, name + '.json')
        with open(json_fname, 'w') as fh:
            json.dump(return_dict, fh, indent=2)
            fh.write('\n')

        return return_dict


class InvokeCACTIP(Invoke):
    '''
    Environment class to invoke CACTI-P.
    '''

    def __init__(self, output_dir, cfg_dir=None, log_dir=None, cacti_path=None):
        super().__init__(output_dir, cfg_dir=cfg_dir,
                         log_dir=log_dir, cacti_path=cacti_path)

        self.cfg_cls = config.ConfigCACTIP
        self.res_cls = result_parser.ResultParserCACTIP

