import ast
import json
import re
import vim
import pep8
import pyflakes.api
from collections import namedtuple

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
        self.errors.append((0, 0, 'unexpected error: ' + msg, 'E'))

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

def check_buffer():
    file = vim.current.buffer.name
    bufnr = vim.current.buffer.number
    messages = []

    pyflakesrep = PyFlakesReporter()
    with open(file, 'U') as f:
        pyflakes.api.check(f.read(), file, pyflakesrep)
    messages.extend(pyflakesrep.errors)

    if not pyflakesrep.has_syntax_error:
        # configure ignored warnings in pep8 user config: http://pep8.readthedocs.org/en/latest/intro.html#configuration
        style = pep8.StyleGuide(reporter=Pep8Report)
        style.input_file(file)
        messages.extend(style.options.report.errors)

    # will clear and toggle the error window when errors is empty
    vim.command('call setqflist({}, "r") | cw'.format(json.dumps([dict(bufnr=bufnr, lnum=m.line, col=m.col, text=m.message, type=m.type) for m in messages])))

    clear_signs()
    for i, msg in enumerate(messages):
        vim.command('sign place {} name=pycheck_{} line={} buffer={}'.format(110 + i, msg.type, msg.line, bufnr))
