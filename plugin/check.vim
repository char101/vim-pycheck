if exists('g:loaded_pycheck')
	finish
endif
let g:loaded_pycheck = 1

sign define pycheck_E text=E! texthl=Error
sign define pycheck_W text=W! texthl=Search

func s:CheckBuffer()
	if exists('b:pycheck_version')
		let python_ver = b:pycheck_version
	else
		let python_ver = exists('g:pycheck_default_version') ? g:pycheck_default_version : 2
		let shebang = getline(1)
		if python_ver == 2
			if shebang =~# '^#!.*\(python\|pypy\)3'
				let python_ver = 3
			endif
		elseif python_ver == 3
			if shebang =~# '^#!.*\(python\|pypy\)\(2\|\>\)'
				let python_ver = 2
			endif
		endif
	endif
	echo "Using python version ".python_ver
	if python_ver == 3
		py3 import pycheck; pycheck.check_buffer()
	else
		py import pycheck; pycheck.check_buffer()
	endif
endf

au BufWritePost *.py call s:CheckBuffer()