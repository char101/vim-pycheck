## pycheck

Check python code for errors using pep8 and pyflakes. Since pep8 and pyflakes are called in-process using the embedded python interpreter,
the checking process is much faster compared to executing external programs.

Since pyflakes uses the internal python compiler to check for syntax errors, the same python version must be used to run pyflakes, i.e.
python 2 should be used to check python 2 code and likewise for python 3.

When python 2 and python 3 support are compiled, it will detect and use the correct python version of the buffer from the shebang line.

### Requirements

* pep8
* pyflakes
