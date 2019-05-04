from clang.cindex import Index, CursorKind

import config
from tree import Location, Coordinate


class Parser:
    def __init__(self):
        config.init_clang()
        self.index = Index.create()
        self.blocks = {}

    def parse(self, filename, flags=None):
        if flags is None:
            flags = config.get_ccflags()

        tu = self.index.parse(filename, flags)

        for node in tu.cursor.get_children():
            if node.location.file.name != filename:
                continue

            if node.kind in (CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD):
                self.process_function(node)
            elif node.kind == CursorKind.CLASS_DECL:
                self.process_class(node)

    def process_class(self, class_node):
        for node in class_node.get_children():
            if node.kind == CursorKind.CXX_METHOD:
                self.process_function(node)

    def process_function(self, fn_node):
        fn_parser = FunctionParser(fn_node)
        fn_parser.parse()
        if fn_parser.has_statements():
            self.blocks[fn_parser.name] = fn_parser.statements


class FunctionParser:
    def __init__(self, fn_node):
        self.fn_node = fn_node
        self.statements = []

    @property
    def name(self):
        return self.fn_node.get_usr()

    def has_statements(self):
        return len(self.statements) > 0

    def parse(self):
        print(self.name)

        children = self.fn_node.get_children()
        curly_blocks = [node for node in children if node.kind == CursorKind.COMPOUND_STMT]

        if len(curly_blocks) == 0:
            return

        block = curly_blocks[0]
        self.traverse(block)

    def traverse(self, node, level=0):
        indent = '  ' * level

        for child in node.get_children():
            print(indent, child.kind, child.spelling)
            self.traverse(child, level + 1)


class ClangLocation(Location):
    def __init__(self, node):
        filename = node.location.file.name
        start = ClangCoordinate(node.extent.start)
        end = ClangCoordinate(node.extent.end)
        super().__init__(filename, start, end)


class ClangCoordinate(Coordinate):
    def __init__(self, source_location):
        super().__init__(source_location.line, source_location.column)
