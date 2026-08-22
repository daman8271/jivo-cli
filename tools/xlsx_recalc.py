"""Recalculate .xlsx formulas via Excel — WITHOUT touching the user's own Excel.

Why this file exists
--------------------
openpyxl writes formulas with no cached value, so a workbook we generate reads
back as all `None` until Excel computes it. The obvious recipe is wrong and
destructive:

    xl = win32com.client.Dispatch('Excel.Application')   # <-- BUG
    ...
    xl.Quit()                                            # <-- kills YOUR Excel

`Dispatch` binds to the Excel instance already running on the desktop (COM
Running Object Table). `Quit()` then shuts that instance down, closing every
workbook the user had open — silently, if DisplayAlerts was turned off.

`DispatchEx` forces a brand-new, private Excel process instead. We only ever
Quit the process we started, so the user's session is untouched.

Usage:  python tools/xlsx_recalc.py <file.xlsx> [more.xlsx ...]
Import: from xlsx_recalc import recalc; recalc(path)
"""

import os
import sys

import pythoncom
import win32com.client as win32

# xlCalculationAutomatic
_XL_AUTOMATIC = -4105


def recalc(path, verbose=True):
    """Open `path` in a private Excel instance, full-rebuild, save, close.

    Raises RuntimeError if the file is locked by another Excel (e.g. the user
    has it open) rather than silently failing to save.
    """
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    # A stale/live lock file means someone (probably the user) has it open.
    lock = os.path.join(os.path.dirname(path), "~$" + os.path.basename(path))
    if os.path.exists(lock):
        raise RuntimeError(
            "%s appears to be open in Excel already (%s exists). "
            "Close it there first — refusing to touch it." % (path, lock)
        )

    pythoncom.CoInitialize()
    xl = win32.DispatchEx("Excel.Application")  # private process, NOT the user's
    try:
        xl.Visible = False
        xl.DisplayAlerts = False  # safe: scoped to our own instance
        xl.Calculation = _XL_AUTOMATIC
        wb = xl.Workbooks.Open(path, UpdateLinks=0)
        try:
            if wb.ReadOnly:
                raise RuntimeError(
                    "%s opened read-only (locked elsewhere); not saving." % path
                )
            xl.CalculateFullRebuild()
            wb.Save()
            if verbose:
                print("recalculated: %s" % path)
        finally:
            wb.Close(SaveChanges=False)
    finally:
        xl.Quit()  # safe: only ever our own instance
        del xl
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python xlsx_recalc.py <file.xlsx> [...]")
    for p in sys.argv[1:]:
        recalc(p)
