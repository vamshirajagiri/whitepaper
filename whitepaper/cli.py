# whitepaper/cli.py
from .utils import print_logo
from .shell import WhitepaperShell

def run_cli():
    # print the logo once per session
    print_logo()
    shell = WhitepaperShell()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        # friendly exit on Ctrl-C
        print("\nExiting Whitepaper...")
