import logging

import cpp_parser

logging.basicConfig(level=logging.DEBUG)

parser = cpp_parser.Parser()
parser.parse('example.cc')
