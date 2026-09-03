# -*- coding: utf-8 -*-
"""Sube los play-by-play como assets de una release de GitHub.

    python scripts/publicar_pbp.py            # sube data/PLAYBYPLAY_*.csv
    python scripts/publicar_pbp.py --bajar    # los trae de vuelta

Los ocho PLAYBYPLAY_*.csv son 387,8 MB de los 409,8 que quedaban en data/: el
95% del peso en el 9% de los archivos. El robot los reescribe enteros cinco
veces al dia, y git guarda una version nueva de cada uno cada vez, asi que en
temporada el repositorio engorda varios GB sin que nadie toque nada. Los assets
de una release no entran en el historial.

La release tiene etiqueta fija (`datos`) y cada asset conserva el nombre del
CSV mas `.gz`, asi que la direccion de descarga no cambia y la API no tiene que
preguntar cual es la ultima.

Necesita `gh` autenticado. En GitHub Actions eso lo da `GH_TOKEN`.
"""
import argparse
import gzip
import json
import pathlib
import shutil
import subprocess
import sys

BASE = pathlib.Path(__file__).resolve().parents[1]
DATOS = BASE / "data"
ETIQUETA = "datos"
PATRON = "PLAYBYPLAY_*.csv"

# Por debajo de esta parte de lo ya publicado no se sube. Ver `_no_encoge`.
MINIMO_DEL_PUBLICADO = 0.6


def _assets_publicados():
    """{nombre: tamaño} de lo que hay ahora mismo en la release."""
    salida = subprocess.run(
        ["gh", "release", "view", ETIQUETA, "--json", "assets"],
        cwd=BASE, capture_output=True, text=True)
    if salida.returncode != 0:
        return {}
    try:
        return {a["name"]: int(a.get("size") or 0)
                for a in json.loads(salida.stdout).get("assets", [])}
    except (ValueError, TypeError, KeyError):
        return {}


def _no_encoge(nombre, tam, publicados):
    """¿El archivo nuevo se parece al que ya está publicado?

    Es la red que faltó en EUROLEAGUE_REPORT el 1 de septiembre de 2026: una
    pasada en pretemporada construyó un dataset de 0,0 MB que estuvo a punto de
    reemplazar los 83,7 MB buenos. Aquí el riesgo es el mismo: si la FEB
    responde a medias, el CSV sale truncado y se publicaría igual.

    Un play-by-play legítimo puede encoger un poco —se corrige un partido, se
    recalcula una jornada— pero no a la mitad.
    """
    antes = publicados.get(nombre)
    if not antes:
        return True
    return tam >= antes * MINIMO_DEL_PUBLICADO


def comprimir(csv, destino):
    """El CSV en gzip. Un play-by-play baja de 91 MB a unos 15."""
    with open(csv, "rb") as entrada, gzip.open(destino, "wb", compresslevel=6) as salida:
        shutil.copyfileobj(entrada, salida, length=1024 * 1024)
    return destino.stat().st_size


def bajar():
    """Trae los play-by-play publicados a data/.

    **El robot los necesita antes de trabajar.** `append_and_save` lee el CSV
    que ya existe y le añade los partidos nuevos; si no está, escribe uno solo
    con lo de hoy y se lleva por delante toda la temporada. Como los CSV ya no
    viajan en el repositorio, el checkout llega sin ellos y hay que bajarlos.
    """
    salida = subprocess.run(
        ["gh", "release", "view", ETIQUETA, "--json", "assets"],
        cwd=BASE, capture_output=True, text=True)
    if salida.returncode != 0:
        print(f"no existe la release «{ETIQUETA}»: nada que bajar")
        return 0
    nombres = [a["name"] for a in json.loads(salida.stdout).get("assets", [])
               if a["name"].startswith("PLAYBYPLAY_") and a["name"].endswith(".csv.gz")]
    if not nombres:
        print("la release no tiene play-by-play: nada que bajar")
        return 0
    DATOS.mkdir(parents=True, exist_ok=True)
    for nombre in sorted(nombres):
        comprimido = DATOS / nombre
        destino = DATOS / nombre[:-3]
        subprocess.run(["gh", "release", "download", ETIQUETA, "--pattern", nombre,
                        "--dir", str(DATOS), "--clobber"], cwd=BASE, check=True)
        # Al temporal y luego renombrar: una descarga cortada deja un .parcial
        # que nadie lee, no un CSV truncado con pinta de bueno.
        parcial = destino.with_suffix(destino.suffix + ".parcial")
        with gzip.open(comprimido, "rb") as gz, open(parcial, "wb") as f:
            shutil.copyfileobj(gz, f, length=1024 * 1024)
        parcial.replace(destino)
        comprimido.unlink(missing_ok=True)
        print(f"{destino.name}: {destino.stat().st_size / 1e6:.1f} MB")
    print(f"bajados {len(nombres)} play-by-play")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--notas", default=None, help="descripción de esta versión")
    ap.add_argument("--forzar", action="store_true",
                    help="publicar aunque algún archivo haya encogido")
    ap.add_argument("--bajar", action="store_true",
                    help="traer los publicados a data/ en vez de subir")
    a = ap.parse_args(argv)

    if a.bajar:
        return bajar()

    fuentes = sorted(DATOS.glob(PATRON))
    if not fuentes:
        # En pretemporada esto puede pasar sin que sea un error: no hay nada
        # que publicar y no tiene sentido mandar un correo de fallo.
        print(f"no hay ningún {PATRON} en {DATOS}: nada que publicar")
        return 0

    publicados = _assets_publicados()
    comprimidos, problemas = [], []
    for csv in fuentes:
        destino = DATOS / (csv.name + ".gz")
        tam = comprimir(csv, destino)
        origen_mb = csv.stat().st_size / 1e6
        print(f"{csv.name}: {origen_mb:.1f} MB -> {tam / 1e6:.1f} MB")
        comprimidos.append(destino)
        if not _no_encoge(destino.name, tam, publicados):
            problemas.append((destino.name, publicados[destino.name], tam))

    if problemas and not a.forzar:
        for c in comprimidos:
            c.unlink(missing_ok=True)
        detalle = "; ".join(f"{n}: {antes / 1e6:.1f} MB -> {ahora / 1e6:.1f} MB"
                            for n, antes, ahora in problemas)
        sys.exit(f"eso no es una actualización, es una pérdida ({detalle}). "
                 f"No se sube nada. Con --forzar si de verdad toca.")

    existe = subprocess.run(["gh", "release", "view", ETIQUETA],
                            cwd=BASE, capture_output=True).returncode == 0
    if not existe:
        print(f"creando la release «{ETIQUETA}»")
        subprocess.run(
            ["gh", "release", "create", ETIQUETA, "--title", "Datos publicados",
             "--notes", "Los play-by-play que lee la API. Se reemplazan en cada pasada."],
            cwd=BASE, check=True)

    print("subiendo…")
    subprocess.run(["gh", "release", "upload", ETIQUETA,
                    *[str(c) for c in comprimidos], "--clobber"],
                   cwd=BASE, check=True)
    if a.notas:
        subprocess.run(["gh", "release", "edit", ETIQUETA, "--notes", a.notas],
                       cwd=BASE, check=True)
    for c in comprimidos:
        c.unlink(missing_ok=True)
    print(f"publicados {len(comprimidos)} archivos en la release «{ETIQUETA}»")
    return 0


if __name__ == "__main__":
    sys.exit(main())
