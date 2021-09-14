from .byte_buffer import ByteBuffer

# C macro for short int size
SHRT_MAX = 32767
FFFF = 65535

# Downsampling translate from bitmap
bitmap_translate = {
    0: 2,
    1: 4,
    2: 5,
    3: 10,
    4: 20,
    5: 50,
    7: -1  # -1 for all
}


class RawDataObject:
    def __init__(self, reader_parent):
        self.reader_parent = reader_parent
        self.header = reader_parent.data['raw_data_file_header']
        self.n_channels = self.header['num_channels']

        # Determine whether need to use frequency byte
        self.freq_change = None
        freq_facor_lst = self.header['frequency_factor']
        for chan_id, freq_down in enumerate(freq_facor_lst):
            if freq_down != SHRT_MAX:
                if self.freq_change is None:
                    self.freq_change = dict()
                if freq_down not in self.freq_change.keys():
                    self.freq_change[freq_down] = []
                self.freq_change[freq_down].append(chan_id)

        # Determine which channels are shorted
        shorted_mask = self.header['shorted']
        self.shorted_channel = [i for i, x in enumerate(shorted_mask) if x]

        # Packet list
        self.values_list = []
        self.channels_list = []
        self.subsample_list = []
        self.packet_file_offset = []
        self.last_channel_value = [None] * self.n_channels

    def load_file(self, buf):
        # Event byte: Skip; Read until EOF
        while buf.read() is not None:

            # Second byte: Optional, freq flag
            if self.freq_change is not None:
                res_read = buf.read()
                for i in range(9):
                    if i in bitmap_translate.keys() and res_read & 1:
                        break
                    if i == 8:
                        raise RuntimeWarning(
                            'Frequency byte was expecting a 1 bit but all are 0. Result might'
                            'be faulty.'
                        )
                    res_read >>= 1
                subsample = bitmap_translate[i]
            else:
                subsample = -1

            # Delta masks
            chan_cursor = 0
            chan_double_delta = []
            while chan_cursor < self.n_channels:

                # Every 8 bits, read a new byte. 0 included
                if chan_cursor % 8 == 0:
                    res_read = buf.read()

                # Check if the bit is on
                if res_read & 1:
                    chan_double_delta.append(chan_cursor)

                # Shift the number by 1
                res_read >>= 1
                chan_cursor += 1

            # TODO: This only works for deltabits=8
            # Read the bytes for delta
            delta_values = []
            delta_channels = []
            abs_channels = []
            for channel_id in range(self.n_channels):
                # Check if channel is shorted or not included due to subsample
                if channel_id in self.shorted_channel:
                    continue
                if subsample != -1 and channel_id not in self.freq_change[subsample]:
                    continue

                # If the delta mask is 1, read 2x8 bits
                byte2read = 2 if channel_id in chan_double_delta else 1

                # Read and interpret the result
                res_read = buf.read(num_read=byte2read)

                # Check if the channel is using absolute value
                if res_read == FFFF:
                    abs_channels.append(channel_id)
                else:
                    # Shift to restore discarded bits
                    res_read <<= self.header['discardbits']

                    # Record the channel and delta values
                    delta_values.append(res_read)
                    delta_channels.append(channel_id)

            # Read the absolute values if needed
            abs_values = []
            for channel_abs in abs_channels:
                res_read = buf.read(read_format='i')
                res_read <<= self.header['discardbits']
                abs_values.append(
                    res_read*self.reader_parent.channel_factors[channel_abs]
                )
                self.last_channel_value[channel_abs] = abs_values[-1]

            # Final values for the packet
            values = []
            channels = delta_channels + abs_channels

            # Apply delta to prev values if applicable
            for delta, channel_id in zip(delta_values, delta_channels):
                converted_delta = delta*self.reader_parent.channel_factors[channel_id]
                values.append(
                    self.last_channel_value[channel_id]+converted_delta
                )
                self.last_channel_value[channel_id] = values[-1]
            values += abs_values

            # Finally, record all the results
            self.values_list.append(values)
            self.channels_list.append(channels)
            self.subsample_list.append(subsample)
            self.packet_file_offset.append(buf.cursor)
