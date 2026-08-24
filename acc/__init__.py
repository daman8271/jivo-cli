"""acc — the Accounts workbench.

A real package (not a namespace one) on purpose: `acc/acc.py` puts its own
directory on sys.path when it runs as a script, and a bare `acc.py` there would
otherwise shadow this package and make `import acc.apbatch` fail with
"'acc' is not a package".
"""
