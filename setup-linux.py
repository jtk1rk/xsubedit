from cx_Freeze import setup, Executable

addtional_mods = ['numpy.core._methods', 'numpy.lib.format']

setup(name = 'xSubEdit',
      description = 'xSubEdit subtitle editor',
      version = '1.5.3rc8',
      options = {"build_exe": {"build_exe": "dist/xSubEdit",
                               #"create_shared_zip": False,
                               "packages": ["gi",'idna'],
                               "excludes": ["Tkinter"],
                               'includes': addtional_mods
                               }},
      executables = [Executable(script = "__main__.py",
                                targetName = "xSubEdit",
                                #appendScriptToExe = True,
                                )]
    )