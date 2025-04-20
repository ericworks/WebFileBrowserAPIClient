import json 

class FileItem:
    def __init__(self, name, size, path, extension, modified, mode, isDir, isSymlink, type):
        self.name = name
        self.size = size
        self.path = path
        self.extension = extension
        self.modified = modified
        self.mode = mode
        self.isDir = isDir
        self.isSymlink = isSymlink
        self.type = type

        self.property = dict()

    def __str__(self):
        return f'{self.name}'
    def __repr__(self):
        return f'{json.dumps(self.__dict__)}'
    def __eq__(self, other):
        return self.name == other.name and self.size == other.size and self.path == other.path and self.extension == other.extension and self.modified == other.modified and self.mode == other.mode and self.isDir == other.isDir and self.isSymlink == other.isSymlink and self.type == other.type
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return hash((self.name, self.size, self.path, self.extension, self.modified, self.mode, self.isDir, self.isSymlink, self.type))
    def __lt__(self, other):
        return self.name < other.name
    def __le__(self, other):
        return self.name <= other.name
    def __gt__(self, other):
        return self.name > other.name
    def __ge__(self, other):
        return self.name >= other.name
    def __len__(self):
        return self.size
    def __getitem__(self, key):
        return self.property[key]
    def __setitem__(self, key, value):

        self.property[key] = value
    def __delitem__(self, key):
        del self.property[key]

    