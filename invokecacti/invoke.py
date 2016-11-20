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
from tempfile import NamedTemporaryFile, gettempdir

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

        if cacti_exe is None:
            try:
                cacti_exe = os.path.join(os.environ.get('CACTIPATH'), 'cacti')
            except KeyError:
                raise EnvironmentError('{}: CACTI path is not provided and '
                                       'cannot find env var CACTIPATH.'
                                       .format(self.__class__.__name__))

        if not os.path.isfile(cacti_exe) or not os.access(cacti_exe, os.X_OK):
            raise ValueError('{}: CACTI path or envvar CACTIPATH {} is invalid.'
                             .format(self.__class__.__name__, cacti_exe))
        self.cacti_exe = os.path.abspath(cacti_exe)

        self.output_dir = os.path.abspath(output_dir)
        self.cfg_dir = os.path.abspath(cfg_dir) if cfg_dir is not None else None
        self.log_dir = os.path.abspath(log_dir) if log_dir is not None else None

        self.result_parser = None

    def get_cacti_exe(self):
        ''' Path to CACTI executable. '''
        return self.cacti_exe

    def get_output_dir(self):
        ''' Output directory. '''
        return self.output_dir

    def _make_config(self, **kwargs):
        raise NotImplementedError('{}: _make_config() not implemented.'
                                  .format(self.__class__.__name__))

    def invoke(self, **kwargs):
        '''
        Invoke CACTI for the specific configuration.
        '''

        return_dict = OrderedDict()

        # create config.
        cfg = self._make_config(**kwargs)
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
            with NamedTemporaryFile(suffix='.cfg', delete=False) as tempfh:
                tempfh.write(cfg.generate())
                cfg_fname = tempfh.name

        # run.
        try:
            with open(os.devnull, 'w') as fnull:
                outstr = subprocess.check_output(
                    [self.cacti_exe, '-infile', cfg_fname],
                    stderr=fnull, cwd=gettempdir())
        except subprocess.CalledProcessError as e:
            raise RuntimeError('{}: CACTI exits with {}'
                               .format(self.__class__.__name__, e.returncode))

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
        results = self.result_parser.parse(outstr)

        # compose return dict.
        # update() loses order.
        for key, val in cfg.config_dict().items():
            return_dict[key] = val
        for key, val in results.items():
            return_dict[key] = val

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

    def __init__(self, output_dir, cfg_dir=None, log_dir=None, cacti_exe=None):
        super(InvokeCACTIP, self).__init__(output_dir, cfg_dir=cfg_dir,
                                           log_dir=log_dir, cacti_exe=cacti_exe)
        self.result_parser = result_parser.ResultParserCACTIP()

    def _make_config(self, **kwargs):
        param_dict = OrderedDict()
        try:
            param_dict['SIZE'] = kwargs.pop('size')
            param_dict['WAYS'] = kwargs.pop('assoc')
            param_dict['LINE'] = kwargs.pop('line')
            param_dict['BANKS'] = kwargs.pop('banks', 1)
            param_dict['TECHNODE'] = kwargs.pop('tech', 0.032)
            param_dict['TEMP'] = kwargs.pop('temp', 350)
            param_dict['LEVEL'] = kwargs.pop('level', 'L1')
            param_dict['TYPE'] = kwargs.pop('memtype', 'cache')
            param_dict['RWPORT'] = kwargs.pop('rwports', 0)
            param_dict['RDPORT'] = kwargs.pop('rdports', 1)
            param_dict['WRPORT'] = kwargs.pop('wrports', 1)
            param_dict['DARRAY_CELL_TYPE'] = kwargs.pop('dcell', 'hp')
            param_dict['DARRAY_PERI_TYPE'] = kwargs.pop('dperi', 'hp')
            param_dict['TARRAY_CELL_TYPE'] = kwargs.pop('tcell', 'hp')
            param_dict['TARRAY_PERI_TYPE'] = kwargs.pop('tperi', 'hp')
        except KeyError as e:
            raise TypeError('{}: must provide argument {}.'
                            .format(self.__class__.__name__, str(e)))
        if len(kwargs) > 0:
            raise TypeError('{}: invalid argument(s) {}'
                            .format(self.__class__.__name__, str(kwargs.keys())))

        return config.ConfigCACTIP(param_dict)

