import os
import json
import struct
import collections
from .utils.byte_buffer import ByteBuffer
from .utils.misc import load_json

"""
Documentation for data_template based parsing file.

The json file has to have 2 layers: The first layer being the section 
of data, for example file_content and generic header. The second layer 
contains the actual data. All data should follow this format:

FIELD_NAME: ["VARIABLE_TYPE", NUM_REPS]

For example, for a field called file_guid that is 2 int's long:

file_guid: ["i", 2]

Valid variable types are listed below, either in the list called
unpack_var_size or in the parsing_function. 


Requirement feature:
You can require certain fileds to match your specified values.

TODO: Add doc on requirement
TODO: Add doc on checkpoint
TODO: Add support for inferring base schema
"""


class ReadFileParent:
    def __init__(self, load_filename, data_template_type, base_schema=1):
        self.load_filename = load_filename
        dir_name = os.getcwd()

        if base_schema > 0:
            # First load the generic header data_templates
            generic_data_template_filename = os.path.join(
                dir_name,
                "data_templates/generic_header_data_template_schema_{}.json".format(base_schema)
            )
            self.generic_data_templates = load_json(generic_data_template_filename)
        else:
            # File types without a generic template
            self.generic_data_templates = None

        # Load the file schema specific directories
        self.schema_data_template_dir = os.path.join(dir_name, 'data_templates', data_template_type)

    def load(self):
        self.requirements = {}
        self.data = {}

        buf = ByteBuffer(self.load_filename)
        generic_loaded = False
        for stage in range(2):
            if stage == 0:
                if self.generic_data_templates is None:
                    generic_loaded = True
                else:
                    data_template = self.generic_data_templates
            elif self.generic_data_templates is not None:
                generic_loaded = True
            else:
                # If no generic header is used and finished stage 1
                continue

            if generic_loaded:
                if self.generic_data_templates is None:
                    # When having no base header, there is no file schema
                    data_template_to_load = os.path.join(
                        self.schema_data_template_dir,
                        "data_template.json"
                    )

                else:
                    if not self.validate():
                        raise ValueError("Generic header validation failed!")

                    # Find the file schema described in header
                    file_schema = self.data['generic_file_header']['file_schema']
                    data_template_to_load = os.path.join(
                        self.schema_data_template_dir,
                        "file_schema_{}".format(file_schema),
                        "data_template.json"
                    )
                    self.file_schema = file_schema

                if not os.path.isfile(data_template_to_load):
                    raise FileNotFoundError(
                        "Schema-specific data_template not found. "
                        "File should be: {}".format(data_template_to_load)
                    )

                # Load the correct version of data_templates
                data_template = load_json(data_template_to_load)

            for key_outer, val_outer in data_template.items():
                if "requirements" in key_outer:
                    self.requirements[key_outer.split(":")[1]] = val_outer
                    continue
                elif "special" in key_outer:
                    # If there is a special field, pass to the method
                    self.read_special_field(buf, key_outer.split(":")[1], val_outer)
                    continue
                elif "read_checkpoint" in key_outer:
                    # Run a check on reading offset
                    if buf.cursor != val_outer:
                        raise ValueError("Checkpoint '{}' failed".format(key_outer))
                    continue
                elif "repeat" in key_outer:
                    # When in repeat, read until the end and repeatedly
                    # fill in a dict.
                    key_outer = key_outer.split(":")[1]

                    self.data[key_outer] = dict()
                    for key in val_outer.keys():
                        # Empty list for repeated units
                        self.data[key_outer][key] = []

                    while not buf.isfinished():
                        for key, val in val_outer.items():
                            if isinstance(val[1], int):
                                # Specify plain number as num_reads
                                loaded = buf.read(val[0], val[1])
                            else:
                                # Specify evaluable as num_reads condition
                                d_temp = {}
                                for key_inner in self.data[key_outer].keys():
                                    # Itself can't be used as condition
                                    # TODO: Check for cyclic condition
                                    if key_inner == key: continue
                                    d_temp[key_inner] = \
                                        self.data[key_outer][key_inner][-1]
                                locals().update(d_temp)
                                loaded = buf.read(val[0], eval(val[1]))
                            self.data[key_outer][key].append(loaded)

                    continue

                # TODO: Only support 2 levels of hierarchy for now
                if isinstance(val_outer, dict):
                    self.data[key_outer] = dict()
                    for key, val in val_outer.items():
                        loaded = buf.read(*val)
                        self.data[key_outer][key] = loaded
                else:
                    loaded = buf.read(*val_outer)
                    self.data[key_outer] = loaded

    def validate(self):
        # Iterate through the requirement dict
        for key_outer, val_outer in self.requirements.items():
            for key, val in val_outer.items():
                if self.data[key_outer][key] != val:
                    return False
        return True