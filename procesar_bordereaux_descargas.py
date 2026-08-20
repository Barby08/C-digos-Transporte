# -*- coding: utf-8 -*-
"""
Procesa los ZIP de bordereaux que llegan a la carpeta de Descargas.

Busca archivos .zip en Descargas cuyo nombre empiece con "BORDEREAUX" o "BDX"
(p. ej. "BORDEREAUX ATLAS JULIO 2026.zip", "BORDEREAUX_MAPFRE_JULIO_2026.zip",
"BDX Inbursa.zip"), detecta el mes/anio (del nombre del zip, o si no lo trae,
de los nombres de los archivos que contiene adentro), los descomprime y
copia su contenido a:

    C:\\Users\\IKAL14\\Documents\\Integral\\Marine\\Insumos\\<anio><mes>

Ejemplo: "BORDEREAUX ATLAS JULIO 2026.zip" -> Insumos\\202607\\

Los zip ya procesados se mueven a Descargas\\Procesados para no
volver a procesarlos en la siguiente corrida.

USO:
    python procesar_bordereaux_descargas.py
"""

import os
import re
import sys
import zipfile
import shutil

# Consola a prueba de caracteres unicode (evita crash con acentos/emojis)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# =========================================================================
# CONFIGURACION  <-- edita solo esta seccion
# =========================================================================

# 1) Carpeta donde llegan las descargas.
CARPETA_DESCARGAS = os.path.join(os.path.expanduser("~"), "Downloads")

# 2) Carpeta base de Insumos, dentro se crea la subcarpeta <anio><mes>.
CARPETA_INSUMOS_BASE = r"C:\Users\IKAL14\Documents\Integral\Marine\Insumos"

# 2.5) Carpeta Legacy (dentro de Insumos), para archivos que el notebook lee
#      de ahi en vez de la carpeta mensual (ver ARCHIVOS_LEGACY mas abajo).
CARPETA_LEGACY = os.path.join(CARPETA_INSUMOS_BASE, "Legacy")

# 3) Patrones de nombre para detectar los zip a procesar (comodines, sin
#    importar mayus/minus). Cubre "BORDEREAUX ATLAS...", "BORDEREAUX_MAPFRE_...",
#    "BORDEREAUX BANORTE...", "BDX Inbursa...", etc.
PATRONES_ZIP = ["BORDEREAUX*", "BDX*"]

# 4) Subcarpeta (dentro de Descargas) donde se archivan los zip ya
#    procesados, para no volver a procesarlos la proxima vez.
CARPETA_PROCESADOS = os.path.join(CARPETA_DESCARGAS, "Procesados")

# 5) Si un archivo con el mismo nombre ya existe en destino: "omitir" o
#    "renombrar".
SI_YA_EXISTE = "renombrar"

# 6) Si True, de cada zip solo se extraen los archivos que realmente usa el
#    proceso de Transporte (notebook "1.-Carga de Bases Marine", variables
#    path_bdx_6 a path_bdx_14). El resto del contenido del zip (otros ramos,
#    polizas viejas que ya no se usan, etc.) se ignora.
#    Si False, se extrae todo el contenido del zip (comportamiento anterior).
SOLO_ARCHIVOS_TRANSPORTE = True

# =========================================================================
# FIN DE LA CONFIGURACION
# =========================================================================

# Patrones (regex, insensible a mayus/minus y a espacio/guion bajo) que
# identifican los archivos que SI usa el notebook "1.-Carga de Bases Marine"
# para el proceso de Transporte. Tomados de path_bdx_6..path_bdx_14 en ese
# notebook (Seccion 2: Path Definition and Macrovariables).
PATRONES_ARCHIVOS_TRANSPORTE = [
    r"inbursa[ _]+casco[ _]+pandi[ _]",   # path_bdx_5
    r"inbursa[ _]+casco[ _]+pandi[ _]+transporte[s]?[ _]+09-11",   # path_bdx_6
    r"inbursa[ _]+casco[ _]+pandi[ _]+transporte[s]?[ _]+11-13",   # path_bdx_7
    r"inbursa[ _]+casco[ _]+pandi[ _]+transporte[s]?[ _]+13-15",   # path_bdx_8
    r"ncgl-070-1000773",                                            # path_bdx_10 (Banorte)
    r"atlas[ _]+e01-2-60-3(?!\d)",                                  # path_bdx_11
    r"ncgl-070-1002258",                                            # path_bdx_12 (Mapfre)
    r"atlas[ _]+e01-2-60-10(?!\d)",                                 # path_bdx_13
    r"mapfre[ _]+casco[ _]+pandi[ _]+transportes[ _]+21-23",       # path_bdx_14
]
_RE_ARCHIVOS_TRANSPORTE = [re.compile(p, flags=re.IGNORECASE) for p in PATRONES_ARCHIVOS_TRANSPORTE]


def es_archivo_de_transporte(nombre_archivo):
    """True si el archivo es uno de los que usa el proceso de Transporte."""
    return any(p.search(nombre_archivo) for p in _RE_ARCHIVOS_TRANSPORTE)

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

RE_MES_ANIO = re.compile(
    r"(" + "|".join(MESES.keys()) + r")[\s_]+(\d{4})",
    flags=re.IGNORECASE,
)

MESES_MAYUS = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
]

# Archivos cuyo nombre real (tal como llega en el zip) no coincide con el
# nombre EXACTO que espera el notebook "1.-Carga de Bases Marine" (paths
# hardcodeados en path_bdx_X). Aqui se renombran al extraerlos para que el
# notebook los encuentre sin tener que tocarlos a mano.
# Cada entrada: (regex para detectar el archivo, plantilla del nombre final;
# admite {mes_mayus} y {anio}).
RENOMBRAR_ARCHIVOS = [
    (
        re.compile(r"ncgl-070-1000773", flags=re.IGNORECASE),
        "BDX PEMEX NCGL-070-1000773 - {mes_mayus} {anio}  Casco PandiTransporte y Plataformas.xlsx",
        # path_bdx_10: nombre real trae guiones bajos ("Casco_Pandi_Transporte"),
        # el notebook espera "Casco PandiTransporte" (Pandi y Transporte pegados).
    ),
]


def nombre_final(nombre_original, anio, mes):
    """Si el archivo necesita renombrarse para calzar con el notebook,
    devuelve el nombre esperado; si no, devuelve el nombre original."""
    for patron, plantilla in RENOMBRAR_ARCHIVOS:
        if patron.search(nombre_original):
            return plantilla.format(mes_mayus=MESES_MAYUS[mes - 1], anio=anio)
    return nombre_original


# Archivos que el notebook NO lee de la carpeta mensual (Insumos/<anio><mes>)
# sino de Insumos/Legacy. Se detectan por este patron y se copian ahi con el
# nombre que espera path_bdx_9, en vez de ir a la carpeta del mes.
# Plantilla SIN extension: se conserva la extension real del archivo (el
# path del notebook la trae hardcodeada como .xlsx; si el adjunto real llega
# en .xls se avisa por consola en vez de renombrar a ciegas).
ARCHIVOS_LEGACY = [
    (
        re.compile(r"aguas[ _]+profundas[ _]+12-14", flags=re.IGNORECASE),
        "Bordereaux_Inbursa_Aguas Profundas_12-14_{mes_mayus}_{anio}",
        ".xlsx",  # extension que espera path_bdx_9
    ),
]


def archivo_va_a_legacy(nombre_archivo):
    """True si el archivo debe ir a Insumos/Legacy en vez de a la carpeta mensual."""
    return any(patron.search(nombre_archivo) for patron, _, _ in ARCHIVOS_LEGACY)


def nombre_final_legacy(nombre_original, anio, mes):
    """Nombre final para un archivo que va a Insumos/Legacy, y si su
    extension real no es la que el notebook espera, devuelve tambien un
    aviso (o None si coincide)."""
    ext_real = os.path.splitext(nombre_original)[1]
    for patron, plantilla, ext_esperada in ARCHIVOS_LEGACY:
        if patron.search(nombre_original):
            base = plantilla.format(mes_mayus=MESES_MAYUS[mes - 1], anio=anio)
            aviso = None
            if ext_real.lower() != ext_esperada.lower():
                aviso = (
                    f"el notebook espera extension '{ext_esperada}' pero el archivo "
                    f"real es '{ext_real}'; se conserva '{ext_real}' para no danar el contenido"
                )
            return base + ext_real, aviso
    return nombre_original, None


def extraer_anio_mes(texto):
    """Extrae (anio, mes) de un nombre de archivo. Devuelve None si no encuentra."""
    m = RE_MES_ANIO.search(texto)
    if not m:
        return None
    mes_nombre = m.group(1).lower()
    anio = int(m.group(2))
    mes = MESES[mes_nombre]
    return anio, mes


def extraer_anio_mes_zip(ruta_zip, nombres_internos):
    """Detecta (anio, mes) del zip: primero por su propio nombre; si no trae
    mes/anio (p. ej. "BDX Inbursa.zip"), lo busca en los nombres de los
    archivos que contiene adentro."""
    resultado = extraer_anio_mes(os.path.basename(ruta_zip))
    if resultado:
        return resultado
    for nombre in nombres_internos:
        resultado = extraer_anio_mes(os.path.basename(nombre))
        if resultado:
            return resultado
    return None


def ruta_destino(carpeta_destino, nombre_archivo):
    """Calcula la ruta final del archivo extraido, aplicando SI_YA_EXISTE."""
    destino = os.path.join(carpeta_destino, nombre_archivo)
    if not os.path.exists(destino):
        return destino

    if SI_YA_EXISTE == "omitir":
        return None

    base, ext = os.path.splitext(nombre_archivo)
    i = 1
    while True:
        candidato = os.path.join(carpeta_destino, f"{base}_{i}{ext}")
        if not os.path.exists(candidato):
            return candidato
        i += 1


def procesar_zip(ruta_zip):
    nombre_zip = os.path.basename(ruta_zip)

    try:
        with zipfile.ZipFile(ruta_zip, "r") as zf:
            infolist = zf.infolist()
    except zipfile.BadZipFile:
        print(f"[OMITIDO] '{nombre_zip}': no es un zip valido (¿aun se esta descargando?).")
        return False
    except Exception as e:
        print(f"[OMITIDO] '{nombre_zip}': error al abrirlo ({e}).")
        return False

    nombres_internos = [i.filename for i in infolist if not i.is_dir()]
    resultado = extraer_anio_mes_zip(ruta_zip, nombres_internos)

    if resultado is None:
        print(f"[OMITIDO] '{nombre_zip}': no pude detectar mes/anio (ni en el zip ni en su contenido).")
        return False

    anio, mes = resultado
    anio_mes = f"{anio}{str(mes).zfill(2)}"
    carpeta_destino = os.path.join(CARPETA_INSUMOS_BASE, anio_mes)
    os.makedirs(carpeta_destino, exist_ok=True)

    print(f"[PROCESANDO] '{nombre_zip}'  ->  {anio_mes}")

    try:
        with zipfile.ZipFile(ruta_zip, "r") as zf:
            for info in infolist:
                if info.is_dir():
                    continue
                nombre_archivo = os.path.basename(info.filename)
                if not nombre_archivo:
                    continue

                if archivo_va_a_legacy(nombre_archivo):
                    os.makedirs(CARPETA_LEGACY, exist_ok=True)
                    nombre_salida_legacy, aviso = nombre_final_legacy(nombre_archivo, anio, mes)
                    if aviso:
                        print(f"   ! Aviso ({nombre_archivo}): {aviso}")
                    destino_legacy = ruta_destino(CARPETA_LEGACY, nombre_salida_legacy)
                    if destino_legacy is None:
                        print(f"   - OMITIDO (ya existe en Legacy): {nombre_salida_legacy}")
                        continue
                    with zf.open(info) as origen, open(destino_legacy, "wb") as salida:
                        shutil.copyfileobj(origen, salida)
                    print(f"   + Extraido a Legacy: {os.path.basename(destino_legacy)}")
                    continue

                if SOLO_ARCHIVOS_TRANSPORTE and not es_archivo_de_transporte(nombre_archivo):
                    print(f"   . No usado en Transporte, se ignora: {nombre_archivo}")
                    continue

                nombre_salida = nombre_final(nombre_archivo, anio, mes)
                if nombre_salida != nombre_archivo:
                    print(f"   ~ Renombrado: {nombre_archivo}  ->  {nombre_salida}")

                destino = ruta_destino(carpeta_destino, nombre_salida)
                if destino is None:
                    print(f"   - OMITIDO (ya existe): {nombre_salida}")
                    continue

                with zf.open(info) as origen, open(destino, "wb") as salida:
                    shutil.copyfileobj(origen, salida)
                print(f"   + Extraido: {os.path.basename(destino)}")
    except zipfile.BadZipFile:
        print(f"   ! Error: '{nombre_zip}' no es un zip valido (¿aun se esta descargando?).")
        return False
    except Exception as e:
        print(f"   ! Error al procesar '{nombre_zip}': {e}")
        return False

    # Archivar el zip ya procesado para no reprocesarlo despues.
    try:
        os.makedirs(CARPETA_PROCESADOS, exist_ok=True)
        destino_zip = os.path.join(CARPETA_PROCESADOS, nombre_zip)
        if os.path.exists(destino_zip):
            base, ext = os.path.splitext(nombre_zip)
            i = 1
            while os.path.exists(destino_zip):
                destino_zip = os.path.join(CARPETA_PROCESADOS, f"{base}_{i}{ext}")
                i += 1
        shutil.move(ruta_zip, destino_zip)
    except Exception as e:
        print(f"   ! Aviso: no pude mover el zip a Procesados: {e}")

    return True


def main():
    print(f"Descargas:  {CARPETA_DESCARGAS}")
    print(f"Insumos:    {CARPETA_INSUMOS_BASE}")
    print(f"Patrones zip: {', '.join(PATRONES_ZIP)}")
    print(f"Solo archivos de Transporte: {SOLO_ARCHIVOS_TRANSPORTE}\n")

    if not os.path.isdir(CARPETA_DESCARGAS):
        print(f"[ERROR] No existe la carpeta de descargas: {CARPETA_DESCARGAS}")
        sys.exit(1)

    from fnmatch import fnmatch

    patrones = [p.lower() for p in PATRONES_ZIP]
    zips = [
        f for f in os.listdir(CARPETA_DESCARGAS)
        if f.lower().endswith(".zip") and any(fnmatch(f.lower(), p) for p in patrones)
    ]
    zips = [f for f in zips if os.path.isfile(os.path.join(CARPETA_DESCARGAS, f))]

    if not zips:
        print("No hay zip nuevos de bordereaux en Descargas.")
        return

    print(f"Encontrados {len(zips)} zip por procesar:")
    for z in zips:
        print(f"   - {z}")
    print()

    ok = 0
    for z in zips:
        if procesar_zip(os.path.join(CARPETA_DESCARGAS, z)):
            ok += 1
        print()

    print("-" * 60)
    print(f"Listo. Zip procesados correctamente: {ok}/{len(zips)}")


if __name__ == "__main__":
    main()
