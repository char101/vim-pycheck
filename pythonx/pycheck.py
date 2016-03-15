import json
import re
import sys
from collections import namedtuple

import _ast
import pep8
import vim

from pyflakes import checker
from operator import attrgetter

sign_re = re.compile(r'id=(\d+)\s+name=pycheck')

Message = namedtuple('Message', ['line', 'col', 'message', 'type'])

class Pep8Report(pep8.BaseReport):
    def __init__(self, options):
        pep8.BaseReport.__init__(self, options)
        self.errors = []

    def error(self, lineno, offset, text, check):
        code = pep8.BaseReport.error(self, lineno, offset, text, check)
        if code:
            self.errors.append(Message(self.line_offset + lineno, offset, 'pep8: ' + text, 'W'))
        return code

class PyFlakesReporter:
    def __init__(self):
        self.errors = []
        self.has_syntax_error = False

    def unexpectedError(self, filename, msg):
        self.has_syntax_error = True
        self.errors.append(Message(0, 0, 'unexpected error: ' + msg, 'E'))

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.has_syntax_error = True
        self.errors.append(Message(lineno, offset or 0, 'syntax error: ' + msg, 'E'))

    def flake(self, w):
        self.errors.append(Message(w.lineno, w.col, 'pyflakes: ' + (w.message % w.message_args), 'W'))

def clear_signs():
    bufnr = vim.current.buffer.number
    vim.command('redir => message')
    vim.command('silent execute "sign place buffer={}"'.format(bufnr))
    vim.command('redir END')
    for line in vim.eval('message').split('\n'):
        match = sign_re.search(line)
        if match:
            vim.command('sign unplace {} buffer={}'.format(match.group(1), bufnr))

def can_import_unused(tree):
    """Check if the source only contains import only statements (and optionally assignment and expressions)"""
    invalid_nodes = (_ast.FunctionDef, _ast.ClassDef)
    for node in tree.body:
        if isinstance(node, invalid_nodes):
            return False
    return True

def check_pyflakes(file):
    pyflakesrep = PyFlakesReporter()
    try:
        with open(file, 'U') as f:
            tree = compile(f.read(), file, 'exec', _ast.PyCF_ONLY_AST)
        w = checker.Checker(tree, file)
        allow_unused = can_import_unused(tree)
        for warning in sorted(w.messages, key=attrgetter('lineno')):
            if 'unable to detect undefined names' in warning.message:
                continue
            if allow_unused and 'imported but unused' in warning.message:
                continue
            pyflakesrep.flake(warning)
    except SyntaxError:
        value = sys.exc_info()[1]
        if value.text is not None:
            pyflakesrep.syntaxError(file, value.args[0], value.lineno, value.offset, value.text)
        else:
            pyflakesrep.unexpectedError(file, 'problem decoding source')
    except Exception as ex:
        pyflakesrep.unexpectedError(file, str(ex))
    return pyflakesrep

def check_buffer():
    if len(vim.current.buffer) > 1000:
        return

    ignored_lines = set()
    for i, line in enumerate(vim.current.buffer):
        if line.endswith('#noqa') or line.endswith('# noqa'):
            ignored_lines.add(i + 1)

    file = vim.current.buffer.name
    bufnr = vim.current.buffer.number
    messages = []

    pyflakesrep = check_pyflakes(file)
    messages.extend(pyflakesrep.errors)

    if not pyflakesrep.has_syntax_error:
        # configure pep8 with user settings (http://pep8.readthedocs.org/en/latest/intro.html#configuration)
        style = pep8.StyleGuide(reporter=Pep8Report)
        style.input_file(file)
        messages.extend(style.options.report.errors)

    vim.command('call setqflist({}, "r") | cw'.format(json.dumps([dict(bufnr=bufnr, lnum=m.line, col=m.col, text=m.message, type=m.type) for m in messages if m.line not in ignored_lines])))

    clear_signs()
    for i, msg in enumerate(messages):
        if msg.line is not None and msg.line > 0 and msg.line not in ignored_lines:
            vim.command('sign place {} name=pycheck_{} line={} buffer={}'.format(110 + i, msg.type, msg.line, bufnr))
