import struct
from .key_tree_parser import key_tree_parser

def null_terminated_string(s):
    l = []
    for c in s:
        if c == '\x00':
            break
        l.append(
            c
        )
    return ''.join(l)

class ByteBuffer:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.s = f.read()
        self.cursor = 0
    
    def isfinished(self):
        return self.cursor >= len(self.s) - 1

    def read(self, read_format=None, num_read=1, null_terminate=True):
        """
        Read format can be a string like this: 'iicc', indicating the things to load.
        Read format can also be 'string', indicating to load a string. 
            null_termination can be turned on. num_read indicates
            the max length of the string.
        Read format can be None, in which case plain bytes will be returned
            in the form of int.
        """
        if self.cursor == len(self.s):
            return None

        if read_format is None:
            # Read plain bytes as int
            if num_read == 1:
                val = self.s[self.cursor]
            else:
                val = int.from_bytes(
                    self.s[self.cursor:self.cursor+num_read],
                    'big'
                )
                # Assuming big endian

            self.cursor += num_read
            return val

        elif read_format == 'string' or read_format == 'key_tree':
            if num_read > 0:
                s = self.s[self.cursor:self.cursor+num_read].decode()
                self.cursor += num_read
            else:
                # Will I regret my life over this?
                s = self.s[self.cursor:].decode('ascii', 'ignore')
                # Decodes as raw text

            if null_terminate:
                s = null_terminated_string(s)

            if read_format == 'key_tree':
                s = key_tree_parser(s).to_dict()
            return s

        else:
            # Read using unpack
            updated_format = read_format * num_read
            size_needed = struct.calcsize(updated_format)
            val = struct.unpack(
                updated_format, self.s[self.cursor:self.cursor+size_needed]
            )
            self.cursor += size_needed

            return list(val) if len(updated_format)>1 else val[0]
