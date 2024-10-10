import PyInstaller.__main__

PyInstaller.__main__.run([
    'skykeys_win.py',
    '--onefile',
    '--console'
#    '--add-binary=touch.html:.'
])