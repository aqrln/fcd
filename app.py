import logging
import os

import cpp_parser

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

for checked_name, checked_ast in to_check.blocks.items():
    for compared_name, compared_ast in known_samples.blocks.items():
        similarity = compared_ast.compare(checked_ast)
        if similarity > 0:
            print('comparing {} at {}'.format(checked_name, checked_ast.location))
            print('to        {} at {}'.format(compared_name, compared_ast.location))
            print('similarity: {}'.format(similarity))
            print()
