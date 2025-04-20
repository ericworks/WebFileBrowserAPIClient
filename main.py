import sys
import builtins

# Patch interactive-only exit() to avoid NameError in frozen app
builtins.exit = sys.exit
builtins.quit = sys.exit

import WebFileBrowserAPI
WebFileBrowserAPI.main()