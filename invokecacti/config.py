"""
 * Copyright (c) 2016. Mingyu Gao
 * All rights reserved.
 *
"""

import os
from string import Template


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CFG_TMPL_DIR = os.path.join(_THIS_DIR, 'cfg_templates')


class Config():
    ''' CACTI configuration. '''

    base_config_keys = [
        'SIZE', 'LINE', 'BANKS', 'TECHNODE', 'TEMP', 'TYPE',
        'DARRAY_CELL_TYPE', 'DARRAY_PERI_TYPE',
        'TARRAY_CELL_TYPE', 'TARRAY_PERI_TYPE'
        ]

    def __init__(self, param_dict):
        if not isinstance(param_dict, dict):
            raise TypeError('{}: param_dict has invalid type.'
                            .format(self.__class__.__name__))
        for key in self.base_config_keys:
            if key not in param_dict:
                raise KeyError('{}: key {} is not provided.'
                               .format(self.__class__.__name__, key))
        self.param_dict = param_dict

    def version_name(self):
        '''
        Return the corresponding CACTI version name.
        '''
        raise NotImplementedError('{}: version_name() not implemented.'
                                  .format(self.__class__.__name__))

    def config_keys(self):
        '''
        Return all configuration key names as a list.
        '''
        raise NotImplementedError('{}: config_keys() not implemented.'
                                  .format(self.__class__.__name__))

    def config_name(self):
        '''
        Return a name for this configuration.
        '''
        raise NotImplementedError('{}: config_name() not implemented.'
                                  .format(self.__class__.__name__))

    def config_dict(self):
        '''
        Return the configuration dict.
        '''
        return self.param_dict

    def _format_array_type(self, array_type):
        if array_type in ('itrs-hp', 'itrs-lstp', 'itrs-lop', 'lp-dram', 'comm-dram'):
            return array_type
        if array_type in ('hp', 'lstp', 'lop'):
            return 'itrs-' + array_type
        if array_type == 'dram':
            return 'comm-dram'
        raise ValueError('{}: invalid array type {}.'
                         .format(self.__class__.__name__, array_type))

    def generate(self, filename=None):
        '''
        Generate the cfg file for CACTI.

        Return the cfg file content. If `filename` is not None, also create the
        cfg file.
        '''

        # load template file.

        tmplfilename = os.path.join(_CFG_TMPL_DIR,
                                    '{}.cfg.template'
                                    .format(self.version_name().lower()))
        if not os.path.isfile(tmplfilename):
            raise IOError('{}: template {} does not exist.'
                          .format(self.__class__.__name__, tmplfilename))
        with open(tmplfilename, 'r') as tfile:
            tmpl = Template(tfile.read())

        # check config param dict.

        for key in self.config_keys():
            if key not in self.param_dict:
                raise KeyError('{}: key {} is not provided.'
                               .format(self.__class__.__name__, key))

        type_ = self.param_dict['TYPE']
        if type_ not in ('cache', 'ram', 'cam', 'main memory'):
            raise ValueError('{}: TYPE has invalid value {}.'
                             .format(self.__class__.__name__, type_))

        for key in ['DARRAY_CELL_TYPE', 'DARRAY_PERI_TYPE',
                    'TARRAY_CELL_TYPE', 'TARRAY_PERI_TYPE']:
            self.param_dict[key] = self._format_array_type(self.param_dict[key])

        # fill template.

        content = tmpl.substitute(**self.param_dict)

        if filename is not None:
            with open(filename, 'w') as fh:
                fh.write(content)

        return content


class ConfigCACTIP(Config):
    ''' CACTI-P configuration. '''

    def __init__(self, param_dict):
        super().__init__(param_dict)
        self.param_dict['IOWIDTH'] = 8 * self.param_dict['LINE']

    def version_name(self):
        return 'CACTI-P'

    def config_keys(self):
        return self.base_config_keys \
            + ['WAYS', 'LEVEL', 'RWPORT', 'RDPORT', 'WRPORT', 'IOWIDTH']

    def config_name(self):
        list_ = []
        for key in ['SIZE', 'WAYS', 'LINE', 'BANKS', 'TECHNODE', 'TEMP',
                    'LEVEL', 'TYPE', 'RWPORT', 'RDPORT', 'WRPORT',
                    'DARRAY_CELL_TYPE', 'DARRAY_PERI_TYPE',
                    'TARRAY_CELL_TYPE', 'TARRAY_PERI_TYPE']:
            list_.append(str(self.param_dict[key]))
        return 's{}_w{}_l{}_b{}_t{}_{}k_{}_{}_rw{}_rd{}_wr{}_{}_{}_{}_{}'\
                .format(*list_)

