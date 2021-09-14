from ..file_loading_parent import ReadFileParent


class SNCLoader(ReadFileParent):
    def __init__(self, load_file):
        super().__init__(load_file, "snc")
