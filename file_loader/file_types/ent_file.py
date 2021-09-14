from ..file_loading_parent import ReadFileParent


class ENTLoader(ReadFileParent):
    def __init__(self, load_file):
        super().__init__(load_file, "ent")

# Caution: The last note entry is always None, which needs to be handled with care.