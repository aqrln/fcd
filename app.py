import logging
import os

import cpp_parser
from tree import ASTPrinter

logging.basicConfig(level=logging.WARNING)


def parse_files(root_directory):
    parser = cpp_parser.Parser()

    for directory, _, filenames in os.walk(root_directory):
        for filename in filenames:
            parts = os.path.splitext(filename)
            if len(parts) > 1 and parts[1] in ('.cc', '.cpp', '.h', 'hpp', '.cxx', '.hxx'):
                parser.parse(os.path.join(directory, filename))

    return parser


known_samples = parse_files('known_samples')
to_check = parse_files('to_check')


for fn, ast in known_samples.blocks.items():
    print(fn)
    ast_printer = ASTPrinter(ast)
    ast_printer.print()
