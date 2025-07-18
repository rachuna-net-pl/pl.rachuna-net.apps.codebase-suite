from codebase_suite.commands import commands
import sys

def main():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')
    commands()

if __name__ == "__main__": # pragma: no cover
    main()
