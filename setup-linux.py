from cx_Freeze import setup, Executable

setup(name = 'xSubEdit',
      description = 'xSubEdit subtitle editor',
      version = '1.5.3rc8',
      options = {"build_exe": {"build_exe": "dist/xSubEdit",
                               "create_shared_zip": False,
                               "packages": ["gi"],
                               "excludes": ["Tkinter"]
                               }},
      executables = [Executable(script = "main.py",
                                targetName = "xSubEdit",
                                appendScriptToExe = True,
                                )]
    )