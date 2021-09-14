from ..file_loading_parent import ReadFileParent


class VTCLoader(ReadFileParent):
    def __init__(self, load_file):
        super().__init__(load_file, "vtc", base_schema=-1)
