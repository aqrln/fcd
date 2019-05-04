import logging

import cpp_parser
from tree import ASTPrinter

logging.basicConfig(level=logging.DEBUG)

parser = cpp_parser.Parser()
parser.parse('example.cc')

for fn, ast in parser.blocks.items():
    print(fn)
    ast_printer = ASTPrinter(ast)
    ast_printer.print()
