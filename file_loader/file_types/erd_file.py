import os
from ..file_loading_parent import ReadFileParent
from ..utils.raw_data_packet import RawDataObject
from ..utils.misc import load_json


"""
All keys are evaluatables, and all keys are either dict, list, or string.
TODO: Add doc for conversion file format
"""

class ERDLoader(ReadFileParent):
    def __init__(self, load_file):
        super().__init__(load_file, "erd")
        # TODO: Maybe want to get a centralized class and add files?

    def read_rec(self, val, extra={}):
        """
        Iterate over keys of a dict. 
        If eval() to be bool and true, get
        its value. If it's a list, combine it as string.
        Run eval on the value, etc.
        """

        # Get the dependent variables in locals
        locals().update(self.data['raw_data_file_header'])
        locals().update(extra)

        if isinstance(val, dict):
            for k, v in val.items():

                try:
                    res = eval(k)
                except:
                    raise ValueError('Key {} is not evaluatable'.format(k))

                # Recursion on child dictionaries of matching key
                if isinstance(res, bool) and res:
                    return self.read_rec(v, extra)

            # Shouldn't get here
            raise ValueError(
                "Unmatched version/machine type. Keys are {}.".format(val.keys())
            )

        elif isinstance(val, list):
            return eval(''.join(val))

        elif isinstance(val, str):
            return eval(val)

        else:
            raise ValueError("Invalid configuration of format file")
    
    def correct_electrode_order(self):
        new_lst = [''] * len(self.channel_names)
        header = self.data['raw_data_file_header']
        for virt_chan, phys_chan in enumerate(header['phys_chan']):
            new_lst[virt_chan] = self.channel_names[phys_chan]
        self.channel_names = new_lst

    def read_special_field(self, f, key, val):
        # Path to search for conversion files
        p = os.path.join(
            self.schema_data_template_dir,
            'file_schema_{}'.format(self.file_schema),
            "conversion.json"
        )
        raw_data_conversion = load_json(p)

        # TODO: Handle 4 different headboxes?
        self.data['raw_data_file_header']['headbox_type'] = self.data['raw_data_file_header']['headbox_type'][0]
        self.data['raw_data_file_header']['headbox_sn'] = self.data['raw_data_file_header']['headbox_sn'][0]

        # Get the fields in raw data conversion
        self.num_channels = self.data['raw_data_file_header']['num_channels']
        self.headbox_name = self.read_rec(raw_data_conversion['headbox_name'])
        self.channel_names = self.read_rec(raw_data_conversion['channel_names'])
        self.channel_factors = [0.] * self.data['raw_data_file_header']['num_channels']
        for c_id in range(len(self.channel_factors)):
            self.channel_factors[c_id] = self.read_rec(
                raw_data_conversion['conversion_factors'],
                {'channel':c_id}
            )

        # Actually load .erd file
        o = RawDataObject(self)
        o.load_file(f)
        self.data[key] = o
