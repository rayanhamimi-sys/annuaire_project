"""Mesure la memoire REELLE du processus (RSS) sous Windows.

Equivalent de mesurer_rss.py : le module resource n'existe pas sous Windows.
Chaque approche tourne dans son propre processus, et on releve le pic de
working set (PeakWorkingSetSize), en octets, via GetProcessMemoryInfo.
"""
import subprocess
import sys
from pathlib import Path

if sys.platform != "win32":
    sys.exit("Ce script est la version Windows. Sur macOS ou Linux, lancer mesurer_rss.py.")

# comparer.py est a cote de ce script, pas dans le dossier de travail
# (annuaire-project), ou se trouve donnees/etablissements.csv.
DOSSIER_CORRIGE = Path(__file__).resolve().parent

MESURE = """
import ctypes, sys, time
from ctypes import wintypes

class _Compteurs(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(_Compteurs), wintypes.DWORD]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

sys.path.insert(0, {dossier!r})
from comparer import par_pandas, par_liste, par_generateur
f = {{"pandas": par_pandas, "liste": par_liste, "generateur": par_generateur}}["{nom}"]
t = time.perf_counter()
f()
d = time.perf_counter() - t
c = _Compteurs()
c.cb = ctypes.sizeof(c)
if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb):
    raise ctypes.WinError(ctypes.get_last_error())
print(f"{{d:.1f}} {{c.PeakWorkingSetSize}}")
"""

# PeakWorkingSetSize est en octets (comme ru_maxrss sur macOS).
FACTEUR = 1_048_576

print(f"{'Approche':26s} {'Durée':>8s} {'Pic RSS':>12s}")
print("-" * 48)
for nom, libelle in [("pandas", "pandas (tout en RAM)"),
                     ("liste", "liste (tout en RAM)"),
                     ("generateur", "générateur (en flux)")]:
    code = MESURE.format(nom=nom, dossier=str(DOSSIER_CORRIGE))
    r = subprocess.run(
    [sys.executable, "-c", code],
    capture_output=True,
    text=True,
    check=False,)
    
    if r.returncode:
        print(f"{libelle:26s} ÉCHEC : {r.stderr.strip()[:80]}")
        continue
    duree, rss = r.stdout.split()
    print(f"{libelle:26s} {float(duree):6.1f} s {int(rss)/FACTEUR:9.0f} Mo")
