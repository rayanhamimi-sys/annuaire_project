"""Mesure la memoire REELLE du processus (RSS), pas seulement les allocations Python.

tracemalloc ne voit que ce que l'interpreteur alloue : les buffers numpy de pandas lui
echappent en partie. Chaque approche tourne donc dans son propre processus, et on releve
le pic de RSS via resource.getrusage.
"""
import subprocess
import sys

MESURE = """
import resource, sys, time
sys.path.insert(0, ".")
from comparer import par_pandas, par_liste, par_generateur
f = {{"pandas": par_pandas, "liste": par_liste, "generateur": par_generateur}}["{nom}"]
t = time.perf_counter()
f()
d = time.perf_counter() - t
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(f"{{d:.1f}} {{rss}}")
"""

# macOS renvoie des octets, Linux des kilo-octets
FACTEUR = 1_048_576 if sys.platform == "darwin" else 1024

print(f"{'Approche':26s} {'Durée':>8s} {'Pic RSS':>12s}")
print("-" * 48)
for nom, libelle in [("pandas", "pandas (tout en RAM)"),
                     ("liste", "liste (tout en RAM)"),
                     ("generateur", "générateur (en flux)")]:
    r = subprocess.run(
    [sys.executable, "-c", MESURE.format(nom=nom)],
    capture_output=True,
    text=True,
    check=False,)
    
    if r.returncode:
        print(f"{libelle:26s} ÉCHEC : {r.stderr.strip()[:80]}")
        continue
    duree, rss = r.stdout.split()
    print(f"{libelle:26s} {float(duree):6.1f} s {int(rss)/FACTEUR:9.0f} Mo")
