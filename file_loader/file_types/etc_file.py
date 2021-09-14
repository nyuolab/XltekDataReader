from ..file_loading_parent import ReadFileParent


class ETCLoader(ReadFileParent):
    def __init__(self, load_file):
        super().__init__(load_file, "etc")

    def validate(self, erd_loader=None):
        # First call the super validate
        if not super().validate():
            return False
        
        if erd_loader is not None:
            # Iterate over all toc entries and check the offset
            for toc_step in range(len(self.data['offset'])):
                offset = self.data['offset'][toc_step]
                sample_num = self.data['sample_num'][toc_step]
                sample_span = self.data['sample_span'][toc_step]

                if offset not in erd_loader.data['data_packets'].packet_file_offset:
                    return False


        # That's all for now I guess
        return True
