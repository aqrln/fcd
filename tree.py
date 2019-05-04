class Coordinate:
    def __init__(self, line, column):
        self.line = line
        self.column = column

    def __repr__(self):
        return 'Coordinate({}, {})'.format(repr(self.line), repr(self.column))


class Location:
    def __init__(self, filename, start, end):
        self.filename = filename
        self.start = start
        self.end = end

    def __repr__(self):
        return 'Location({}, {}, {})'.format(repr(self.filename), repr(self.start), repr(self.end))


class CoercionError(Exception):
    pass


class ASTNode:
    def __init__(self, location):
        self.location = location
        self.weight = 1
        self.children = []

    def append_child(self, node):
        self.children.append(node)

    def nth_child(self, index):
        if len(self.children) > index:
            return self.children[index]
        else:
            return NullStatement(self.location)

    def has_children(self):
        return len(self.children) > 0

    def compare(self, other):
        if isinstance(other, type(self)):
            return self.compare_same_type_weighted(other)
        try:
            return self.coerce_and_compare(other)
        except CoercionError:
            return 0

    def coerce_and_compare(self, other):
        try:
            return self.compare_same_type_weighted(other.make_alike(self))
        except CoercionError:
            return other.compare_same_type_weighted(self.make_alike(other))

    def compare_same_type_weighted(self, other):
        return self.compare_same_type(other) * self.combined_weight(other)

    def compare_same_type(self, other):
        if self == other:
            return 1
        else:
            return 0

    def combined_weight(self, other):
        return self.weight * other.weight

    def make_alike(self, other):
        if isinstance(other, NullStatement):
            pseudo_node = NullStatement(self.location)
            pseudo_node.weight = 0.1
            return pseudo_node
        raise CoercionError

    def compare_twice(self, other, get_left, get_right):
        left_score = get_left(self).compare(get_left(other))
        right_score = get_right(self).compare(get_right(other))
        if left_score == 0 or right_score == 0:
            return 0
        return (left_score + right_score) / 2


class RootNode(ASTNode):
    def compare_same_type(self, other):
        return 1


class NullStatement(ASTNode):
    def compare_same_type(self, other):
        return 1


class UnknownStatement(ASTNode):
    def compare_same_type(self, other):
        return 0


class Identifier(ASTNode):
    def __init__(self, name, location):
        super().__init__(location)
        self.name = name

    def compare_same_type(self, other):
        if self.name == other.name:
            return 1
        else:
            return 0


class Assignment(ASTNode):
    @property
    def left(self):
        return self.nth_child(0)

    @property
    def right(self):
        return self.nth_child(1)

    def compare_same_type(self, other):
        return self.compare_twice(other, lambda x: x.left, lambda x: x.right)


class Literal(ASTNode):
    def __init__(self, value, location):
        super().__init__(location)
        self.value = value

    def compare_same_type(self, other):
        score = self.combined_weight(other)
        if self.value == other.value:
            return score
        elif isinstance(other.value, type(self.value)):
            return 0.5 * score
        else:
            return 0.2 * score


class ReturnStatement(ASTNode):
    @property
    def result(self):
        return self.nth_child(0)

    def compare_same_type(self, other):
        return self.result.compare(other.result)


class UnaryOperation(ASTNode):
    def __init__(self, operation, location):
        super().__init__(location)
        self.operation = operation

    @property
    def operand(self):
        return self.nth_child(0)

    def compare_same_type(self, other):
        if self.operation != other.operation:
            return 0
        return self.operand.compare(other.operand)


class BinaryOperation(ASTNode):
    def __init__(self, operation, location):
        super().__init__(location)
        self.operation = operation

    @property
    def left(self):
        return self.nth_child(0)

    @property
    def right(self):
        return self.nth_child(1)

    def compare_same_type(self, other):
        if self.operation != other.operation:
            return 0
        return self.compare_twice(other, lambda x: x.left, lambda x: x.right)


class CStyleLoop(ASTNode):
    @property
    def initializer(self):
        return self.nth_child(0)

    @property
    def condition(self):
        return self.nth_child(1)

    @property
    def statement(self):
        return self.nth_child(2)

    @property
    def body(self):
        return self.nth_child(3)


class ASTBuilder:
    def __init__(self):
        self.nodes_stack = []

    @property
    def product(self):
        return self.nodes_stack[0]

    @property
    def current_node(self):
        return self.nodes_stack[-1]

    def open_root(self, location):
        self.nodes_stack.append(RootNode(location))

    def add_identifier(self, name, location):
        self.add_leaf(Identifier(name, location))

    def add_literal(self, value, location):
        self.add_leaf(Literal(value, location))

    def add_unknown(self, location):
        self.add_leaf(UnknownStatement(location))

    def add_null(self, location):
        self.add_leaf(NullStatement(location))

    def open_assignment(self, location):
        self.add_nonleaf(Assignment(location))

    def open_return(self, location):
        self.add_nonleaf(ReturnStatement(location))

    def close_node(self):
        self.nodes_stack.pop()

    def add_leaf(self, node):
        self.current_node.append_child(node)

    def add_nonleaf(self, node):
        self.current_node.append_child(node)
        self.nodes_stack.append(node)


class ASTPrinter:
    def __init__(self, root):
        self.root = root

    def print(self):
        self.print_node(self.root, 0)

    def print_node(self, node, level):
        indent = '  ' * level
        print(indent, node)
        for child in node.children:
            self.print_node(child, level + 1)
