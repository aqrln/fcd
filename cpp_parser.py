import logging

import clang.cindex
from clang.cindex import Index, CursorKind, Cursor

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
        if isinstance(node, NullCursorSentinel):
            self.process_null(node)
        elif node.kind == CursorKind.DECL_STMT:
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
        elif node.kind == CursorKind.FOR_STMT:
            self.process_for_stmt(node)
        elif node.kind == CursorKind.BINARY_OPERATOR:
            self.process_binary_operator(node)
        elif node.kind == CursorKind.COMPOUND_STMT:
            self.process_compound_stmt(node)
        elif node.kind == CursorKind.UNARY_OPERATOR:
            self.process_unary_operator(node)
        elif node.kind == CursorKind.COMPOUND_ASSIGNMENT_OPERATOR:
            self.process_compound_assignment_operator(node)
        elif node.kind == CursorKind.IF_STMT:
            self.process_if_stmt(node)
        elif node.kind == CursorKind.BREAK_STMT:
            self.process_break_stmt(node)
        elif node.kind == CursorKind.CONTINUE_STMT:
            self.process_continue_stmt(node)
        elif node.kind == CursorKind.WHILE_STMT:
            self.process_while_stmt(node)
        elif node.kind == CursorKind.STRING_LITERAL:
            self.process_string_literal(node)
        elif node.kind == CursorKind.FLOATING_LITERAL:
            self.process_floating_literal(node)
        else:
            self.process_unknown(node)

    def process_children(self, node):
        for child in node.get_children():
            self.process_node(child)

    def process_null(self, node):
        self.builder.add_null(node.location)

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
        token = next(node.get_tokens())
        self.builder.add_literal(token.spelling, ClangLocation(node))

    def process_unexposed_expr(self, node):
        self.process_children(node)

    def process_return_stmt(self, node):
        self.builder.open_return(ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    def process_decl_ref_expr(self, node):
        self.builder.add_identifier(node.spelling, ClangLocation(node))

    def process_for_stmt(self, node):
        self.builder.open_cstyle_loop(ClangLocation(node))
        self.process_children(NullAwareCursorAdapter.from_cursor(node))
        self.builder.close_node()

    def process_binary_operator(self, node):
        self.builder.open_binary_operation(self.get_operation(node), ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    def process_unary_operator(self, node):
        self.builder.open_unary_operation(self.get_operation(node), ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    @staticmethod
    def get_operation(node):
        children_extents = [child.extent for child in node.get_children()]
        for token in node.get_tokens():
            for extent in children_extents:
                if token.extent in extent or token.extent == extent:
                    break
            else:
                return token.spelling
        return ''

    def process_compound_stmt(self, node):
        self.builder.open_block(ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    def process_compound_assignment_operator(self, node):
        operation = self.get_operation(node)[:-1]
        self.builder.open_compound_assignment(operation, ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    def process_if_stmt(self, node):
        self.builder.open_if_statement(ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    def process_break_stmt(self, node):
        self.builder.add_break(ClangLocation(node))

    def process_continue_stmt(self, node):
        self.builder.add_continue(ClangLocation(node))

    def process_while_stmt(self, node):
        self.builder.open_while_statement(ClangLocation(node))
        self.process_children(node)
        self.builder.close_node()

    def process_string_literal(self, node):
        token = next(node.get_tokens())
        self.builder.add_literal(token.spelling, ClangLocation(node))

    def process_floating_literal(self, node):
        token = next(node.get_tokens())
        self.builder.add_literal(token.spelling, ClangLocation(node))


class NullCursorSentinel:
    def __init__(self, parent):
        self.parent = parent
        self.left = None
        self.right = None

    @property
    def start(self):
        node = self.left or self.parent
        return ClangLocation(node).start

    @property
    def end(self):
        node = self.right or self.parent
        return ClangLocation(node).end

    @property
    def location(self):
        return Location(self.parent.location.file.name, self.start, self.end)


class NullAwareCursorAdapter(Cursor):
    def get_children(self):
        def visitor(child, _, current_children):
            if child == clang.cindex.conf.lib.clang_getNullCursor():
                current_children.append(NullCursorSentinel(self))
            else:
                child._tu = self._tu
                current_children.append(child)
            return 1

        children = []
        clang.cindex.conf.lib.clang_visitChildren(self,
                                                  clang.cindex.callbacks['cursor_visit'](visitor),
                                                  children)

        self.resolve_null_extents(children, 'left')
        self.resolve_null_extents(reversed(children), 'right')

        return iter(children)

    @staticmethod
    def resolve_null_extents(cursors, direction):
        for index, cursor in enumerate(cursors):
            if not isinstance(cursor, NullCursorSentinel):
                continue

            if index > 0:
                sibling = cursors[index - 1]
                if isinstance(sibling, NullCursorSentinel):
                    sibling = getattr(sibling, direction)
                setattr(cursor, direction, sibling)

    @classmethod
    def from_cursor(cls, cursor):
        cursor.__class__ = cls
        return cursor


class ClangLocation(Location):
    def __init__(self, node):
        filename = node.location.file.name
        start = ClangCoordinate(node.extent.start)
        end = ClangCoordinate(node.extent.end)
        super().__init__(filename, start, end)


class ClangCoordinate(Coordinate):
    def __init__(self, source_location):
        super().__init__(source_location.line, source_location.column)
