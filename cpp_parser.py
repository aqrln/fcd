import logging

from clang.cindex import Index, CursorKind

import config
from tree import Location, Coordinate, ASTBuilder


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
        self.builder = ASTBuilder()
        self.builder.open_root(ClangLocation(fn_node))

    @property
    def name(self):
        return self.fn_node.get_usr()

    @property
    def statements(self):
        return self.builder.product

    def has_statements(self):
        return self.statements.has_children()

    def parse(self):
        logging.debug('%s', self.name)

        children = self.fn_node.get_children()
        curly_blocks = [node for node in children if node.kind == CursorKind.COMPOUND_STMT]

        if len(curly_blocks) == 0:
            return

        block = curly_blocks[0]
        self.traverse(block)

        for node in block.get_children():
            self.process_node(node)

    def traverse(self, node, level=1):
        indent = '  ' * level

        for child in node.get_children():
            logging.debug('%s %s %s', indent, child.kind, child.spelling)
            self.traverse(child, level + 1)

    def process_node(self, node):
        if node.kind == CursorKind.DECL_STMT:
            self.process_decl(node)
        elif node.kind == CursorKind.VAR_DECL:
            self.process_var_decl(node)
        elif node.kind == CursorKind.INTEGER_LITERAL:
            self.process_integer_literal(node)
        elif node.kind == CursorKind.UNEXPOSED_EXPR:
            self.process_unexposed_expr(node)
        elif node.kind == CursorKind.RETURN_STMT:
            self.process_return_stmt(node)
        elif node.kind == CursorKind.DECL_REF_EXPR:
            self.process_decl_ref_expr(node)
        else:
            self.process_unknown(node)

    def process_children(self, node):
        for child in node.get_children():
            self.process_node(child)

    def process_decl(self, node):
        self.process_children(node)

    def process_var_decl(self, node):
        self.builder.open_assignment(ClangLocation(node))
        self.builder.add_identifier(node.spelling, ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    def process_unknown(self, node):
        logging.warning('[FunctionParser] unknown %s', node.kind)
        self.builder.add_unknown(ClangLocation(node))

    def process_integer_literal(self, node):
        self.builder.add_literal(0, ClangLocation(node))  # TODO

    def process_unexposed_expr(self, node):
        self.process_children(node)

    def process_return_stmt(self, node):
        self.builder.open_return(ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    def process_decl_ref_expr(self, node):
        self.builder.add_identifier(node.spelling, ClangLocation(node))


class ClangLocation(Location):
    def __init__(self, node):
        filename = node.location.file.name
        start = ClangCoordinate(node.extent.start)
        end = ClangCoordinate(node.extent.end)
        super().__init__(filename, start, end)


class ClangCoordinate(Coordinate):
    def __init__(self, source_location):
        super().__init__(source_location.line, source_location.column)
