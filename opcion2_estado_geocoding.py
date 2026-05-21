"""
OPCION 2 - Clasificador con API de Geocodificacion (Nominatim/OpenStreetMap)
Usa geopy para geocodificar texto libre y obtener el estado.
Dependencias: pandas, geopy, unidecode

Como funciona:
  1. Normaliza el texto de LOCATION
  2. Intenta geocodificar con Nominatim (OpenStreetMap, gratuito)
  3. De la respuesta extrae estado/pais
  4. Cache en disco para no repetir llamadas
  5. Fallback a clasificador offline si la API no responde

Ventajas:
  - Cubre practicamente CUALQUIER ubicacion, incluso las no catalogadas
  - Resuelve coordenadas geograficas automaticamente
  - No requiere mantener catalogos manuales

Desventajas:
  - Requiere internet
  - Nominatim limita a 1 request/segundo (4K filas = ~70 min sin cache)
  - Resultados pueden variar entre ejecuciones
  - No es 100% reproducible

NOTA: Para uso en produccion, considerar usar un servicio pagado
(Google Maps, Mapbox) que permita batch geocoding.
"""

import pandas as pd
import re
import json
import os
import time
import hashlib
from unidecode import unidecode

try:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    GEOPY_DISPONIBLE = True
except ImportError:
    GEOPY_DISPONIBLE = False
    print("AVISO: geopy no instalado. Instalar con: pip install geopy")


# ============================================================
# CACHE EN DISCO (evita llamadas repetidas a la API)
# ============================================================
CACHE_FILE = "geocoding_cache.json"

def cargar_cache(path=CACHE_FILE):
    """Carga cache de geocodificacion desde disco."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_cache(cache, path=CACHE_FILE):
    """Guarda cache de geocodificacion a disco."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# ============================================================
# MAPEO DE ESTADOS (Nominatim usa nombres completos)
# ============================================================
NOMINATIM_TO_ESTADO = {
    "Aguascalientes": "AGUASCALIENTES",
    "Baja California": "BAJA CALIFORNIA",
    "Baja California Sur": "BAJA CALIFORNIA SUR",
    "Campeche": "CAMPECHE",
    "Chiapas": "CHIAPAS",
    "Chihuahua": "CHIHUAHUA",
    "Coahuila de Zaragoza": "COAHUILA",
    "Coahuila": "COAHUILA",
    "Colima": "COLIMA",
    "Ciudad de Mexico": "CIUDAD DE MEXICO",
    "Ciudad de México": "CIUDAD DE MEXICO",
    "Durango": "DURANGO",
    "Guanajuato": "GUANAJUATO",
    "Guerrero": "GUERRERO",
    "Hidalgo": "HIDALGO",
    "Jalisco": "JALISCO",
    "Mexico": "ESTADO DE MEXICO",
    "México": "ESTADO DE MEXICO",
    "Michoacan de Ocampo": "MICHOACAN",
    "Michoacán de Ocampo": "MICHOACAN",
    "Michoacan": "MICHOACAN",
    "Morelos": "MORELOS",
    "Nayarit": "NAYARIT",
    "Nuevo Leon": "NUEVO LEON",
    "Nuevo León": "NUEVO LEON",
    "Oaxaca": "OAXACA",
    "Puebla": "PUEBLA",
    "Queretaro": "QUERETARO",
    "Querétaro": "QUERETARO",
    "Quintana Roo": "QUINTANA ROO",
    "San Luis Potosi": "SAN LUIS POTOSI",
    "San Luis Potosí": "SAN LUIS POTOSI",
    "Sinaloa": "SINALOA",
    "Sonora": "SONORA",
    "Tabasco": "TABASCO",
    "Tamaulipas": "TAMAULIPAS",
    "Tlaxcala": "TLAXCALA",
    "Veracruz de Ignacio de la Llave": "VERACRUZ",
    "Veracruz": "VERACRUZ",
    "Yucatan": "YUCATAN",
    "Yucatán": "YUCATAN",
    "Zacatecas": "ZACATECAS",
}

# Paises
PAISES_CONOCIDOS = {
    "United States": "USA",
    "Estados Unidos": "USA",
    "Panama": "PANAMA",
    "Panamá": "PANAMA",
    "Chile": "CHILE",
    "Germany": "ALEMANIA",
    "Alemania": "ALEMANIA",
    "Singapore": "SINGAPUR",
    "Netherlands": "PAISES BAJOS",
}


# ============================================================
# NORMALIZACION DE TEXTO PARA GEOCODING
# ============================================================
def limpiar_para_geocoding(texto):
    """
    Limpia el texto de LOCATION para mejorar la geocodificacion.
    Elimina ruido como 'KM', 'CARR.', numeros de kilometro, etc.
    """
    if pd.isna(texto) or str(texto).strip() in ("", "-", "nan", "N/A"):
        return ""

    t = str(texto).strip()

    # Quitar patrones de ruido
    t = re.sub(r'KM[\.\s]*\d+[\+\d]*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'CARR[\.\s]*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'CARRT[\.\s]*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'CARRETERA\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'AUTOPISTA\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'AUT[\.\s]+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'AUTP[\.\s]+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'FED[\.\s]*\d*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'LIBRE\s+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'DURANTE SU TRAYECTO DE ', '', t, flags=re.IGNORECASE)
    t = re.sub(r'TAD\s+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'TAR\s+(DE\s+)?', '', t, flags=re.IGNORECASE)
    t = re.sub(r'TASP\s+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'C\.?E\.?\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'TERMINAL\s+(MARITIMA\s+)?', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\d+\s*[DN]\b', '', t)  # 132 D, 40 N
    t = re.sub(r'[;:\[\]\(\)\{\}*#!]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.strip('.,- ')

    # Agregar ", Mexico" si no tiene pais para ayudar a Nominatim
    upper = t.upper()
    paises_mencionados = ["USA", "EUA", "EEUU", "TEXAS", "PANAMA", "CHILE",
                          "SINGAPORE", "ALEMANIA", "AMSTERDAM", "CALIFORNIA",
                          "HOUSTON", "GALVESTON"]
    tiene_pais = any(p in upper for p in paises_mencionados)
    if not tiene_pais and len(t) > 2:
        t = t + ", Mexico"

    return t


# ============================================================
# GEOCODIFICADOR CON CACHE
# ============================================================
def crear_geocodificador():
    """Crea instancia de Nominatim con rate limiter."""
    if not GEOPY_DISPONIBLE:
        return None

    geolocator = Nominatim(
        user_agent="marine_claims_geocoder_v1",
        timeout=10
    )
    # Rate limiter: maximo 1 request por segundo (requisito de Nominatim)
    geocode = RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1.1,
        max_retries=2,
        error_wait_seconds=5.0
    )
    return geocode


def geocodificar_ubicacion(texto_limpio, geocode_fn, cache):
    """
    Geocodifica un texto y extrae estado/pais.
    Usa cache para evitar llamadas repetidas.
    """
    if not texto_limpio:
        return {"estado": "NO ESPECIFICADO", "metodo": "vacio", "confianza": "N/A"}

    # Revisar cache
    cache_key = texto_limpio.lower().strip()
    if cache_key in cache:
        cached = cache[cache_key]
        cached["metodo"] = "cache:" + cached.get("metodo", "geocoding")
        return cached

    if geocode_fn is None:
        return {"estado": "NO IDENTIFICADO", "metodo": "sin_geopy", "confianza": "N/A"}

    try:
        location = geocode_fn(
            texto_limpio,
            language="es",
            addressdetails=True,
            exactly_one=True
        )

        if location is None:
            resultado = {"estado": "NO IDENTIFICADO", "metodo": "sin_resultado", "confianza": "N/A"}
            cache[cache_key] = resultado
            return resultado

        address = location.raw.get("address", {})
        state = address.get("state", "")
        country = address.get("country", "")
        country_code = address.get("country_code", "")

        # Si es Mexico, mapear estado
        if country_code == "mx":
            estado = NOMINATIM_TO_ESTADO.get(state, state.upper())
            resultado = {
                "estado": estado,
                "metodo": "geocoding",
                "confianza": "ALTA",
                "lat": location.latitude,
                "lon": location.longitude,
            }
        else:
            # Internacional
            pais = PAISES_CONOCIDOS.get(country, country.upper())
            resultado = {
                "estado": pais,
                "metodo": "geocoding_intl",
                "confianza": "ALTA",
                "lat": location.latitude,
                "lon": location.longitude,
            }

        cache[cache_key] = resultado
        return resultado

    except Exception as e:
        resultado = {
            "estado": "ERROR",
            "metodo": "error:" + str(e)[:50],
            "confianza": "N/A"
        }
        cache[cache_key] = resultado
        return resultado


# ============================================================
# FUNCION PARA APLICAR A UN DATAFRAME
# ============================================================
def agregar_estado_geocoding(df, col_location="LOCATION", cache_path=CACHE_FILE,
                              max_filas=None, verbose=True):
    """
    Agrega columna ESTADO al DataFrame usando geocodificacion.

    Args:
        df:            DataFrame con columna LOCATION
        col_location:  Nombre de la columna de ubicacion
        cache_path:    Ruta del archivo de cache
        max_filas:     Limite de filas a procesar (None = todas)
        verbose:       Mostrar progreso
    """
    cache = cargar_cache(cache_path)
    geocode_fn = crear_geocodificador()

    if geocode_fn is None:
        print("ERROR: geopy no disponible. Instalar con: pip install geopy")
        return df

    # Obtener valores unicos para minimizar llamadas API
    ubicaciones_unicas = df[col_location].dropna().unique()
    total = len(ubicaciones_unicas)
    if max_filas:
        total = min(total, max_filas)

    if verbose:
        print("Geocodificando {} ubicaciones unicas...".format(total))
        en_cache = sum(1 for u in ubicaciones_unicas[:total]
                       if limpiar_para_geocoding(u).lower().strip() in cache)
        print("  {} ya en cache, {} por consultar".format(en_cache, total - en_cache))

    # Geocodificar valores unicos
    resultados_unicos = {}
    for i, loc in enumerate(ubicaciones_unicas[:total]):
        texto_limpio = limpiar_para_geocoding(loc)
        resultado = geocodificar_ubicacion(texto_limpio, geocode_fn, cache)
        resultados_unicos[loc] = resultado

        if verbose and (i + 1) % 50 == 0:
            print("  Progreso: {}/{} ({:.0f}%)".format(i + 1, total, (i + 1) / total * 100))

        # Guardar cache cada 100 registros
        if (i + 1) % 100 == 0:
            guardar_cache(cache, cache_path)

    # Guardar cache final
    guardar_cache(cache, cache_path)

    if verbose:
        print("  Geocodificacion completa. Cache guardado en: {}".format(cache_path))

    # Aplicar resultados al DataFrame
    def get_resultado(loc):
        if pd.isna(loc):
            return {"estado": "NO ESPECIFICADO", "metodo": "vacio", "confianza": "N/A"}
        return resultados_unicos.get(loc, {"estado": "NO IDENTIFICADO", "metodo": "no_procesado", "confianza": "N/A"})

    resultados = df[col_location].apply(get_resultado)
    df["ESTADO"]        = resultados.apply(lambda r: r["estado"])
    df["METODO_MATCH"]  = resultados.apply(lambda r: r["metodo"])
    df["CONFIANZA"]     = resultados.apply(lambda r: r["confianza"])

    return df


# ============================================================
# OPCION HIBRIDA (RECOMENDADA): Offline primero, API para los que fallan
# ============================================================
def agregar_estado_hibrido(df, col_location="LOCATION", cache_path=CACHE_FILE, verbose=True):
    """
    Estrategia hibrida:
    1. Primero intenta clasificar offline (rapido, sin API)
    2. Solo los 'NO IDENTIFICADO' se envian a geocodificacion (lento, con API)

    Esta es la opcion RECOMENDADA para produccion.
    """
    # Importar clasificador offline
    import importlib.util
    script_dir = os.path.dirname(os.path.abspath(__file__))
    offline_path = os.path.join(script_dir, "opcion1_estado_offline.py")

    if os.path.exists(offline_path):
        spec = importlib.util.spec_from_file_location("offline", offline_path)
        offline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(offline)
        clasificar_offline = offline.clasificar_estado
    else:
        print("AVISO: opcion1_estado_offline.py no encontrado. Usando solo geocoding.")
        clasificar_offline = None

    # Paso 1: Clasificacion offline
    if clasificar_offline:
        if verbose:
            print("Paso 1: Clasificacion offline...")
        resultados_offline = df[col_location].apply(clasificar_offline)
        df["ESTADO"]       = resultados_offline.apply(lambda r: r["estado"])
        df["METODO_MATCH"] = resultados_offline.apply(lambda r: r["metodo"])
        df["CONFIANZA"]    = resultados_offline.apply(lambda r: r["confianza"])

        sin_match = df[df["ESTADO"] == "NO IDENTIFICADO"]
        if verbose:
            print("  {} clasificados offline, {} sin match".format(
                len(df) - len(sin_match), len(sin_match)))
    else:
        sin_match = df

    # Paso 2: Geocodificar solo los que fallaron
    if len(sin_match) > 0 and GEOPY_DISPONIBLE:
        if verbose:
            print("Paso 2: Geocodificando {} registros sin match...".format(len(sin_match)))

        cache = cargar_cache(cache_path)
        geocode_fn = crear_geocodificador()

        ubicaciones_faltantes = sin_match[col_location].dropna().unique()

        for i, loc in enumerate(ubicaciones_faltantes):
            texto_limpio = limpiar_para_geocoding(loc)
            resultado = geocodificar_ubicacion(texto_limpio, geocode_fn, cache)

            # Actualizar filas correspondientes
            mask = df[col_location] == loc
            df.loc[mask, "ESTADO"] = resultado["estado"]
            df.loc[mask, "METODO_MATCH"] = resultado["metodo"]
            df.loc[mask, "CONFIANZA"] = resultado.get("confianza", "N/A")

            if verbose and (i + 1) % 10 == 0:
                print("  Geocoding: {}/{}".format(i + 1, len(ubicaciones_faltantes)))

        guardar_cache(cache, cache_path)
        if verbose:
            print("  Cache guardado: {}".format(cache_path))

    return df


# ============================================================
# EJEMPLO DE USO
# ============================================================
if __name__ == "__main__":

    print("=" * 80)
    print("OPCION 2: GEOCODIFICACION CON NOMINATIM")
    print("=" * 80)

    if not GEOPY_DISPONIBLE:
        print("\nPara usar esta opcion, instala geopy:")
        print("  pip install geopy")
        print("\nMientras tanto, puedes usar la Opcion 1 (offline).")
    else:
        # Ejemplo con datos de prueba
        datos_prueba = pd.DataFrame({"LOCATION": [
            "COATZACOALCOS, VERACRUZ",
            "CARR. MEX-QRO.KM 49",
            "Houston, TX, USA",
            "CDMX Azcapotzalco",
            "ACAPULCO, GRO.",
            "TAD PAJARITOS",
            None,
        ]})

        print("\n--- Geocodificando datos de prueba ---")
        resultado = agregar_estado_geocoding(
            datos_prueba,
            cache_path="geocoding_cache_test.json",
            verbose=True
        )

        print("\n--- Resultados ---")
        for _, row in resultado.iterrows():
            loc = str(row["LOCATION"])[:45].ljust(45)
            est = row["ESTADO"].ljust(25)
            met = row["METODO_MATCH"]
            print("  {} -> {} [{}]".format(loc, est, met))

    # Mostrar uso hibrido
    print("\n" + "=" * 80)
    print("OPCION HIBRIDA (RECOMENDADA)")
    print("=" * 80)
    print("""
    Uso:
        from opcion2_estado_geocoding import agregar_estado_hibrido

        df = pd.read_excel("tu_archivo.xlsx")
        df = agregar_estado_hibrido(df, col_location="LOCATION")

    Esto:
      1. Clasifica offline (~99% de los registros, en segundos)
      2. Solo geocodifica los que no se pudieron clasificar (~1%)
      3. Guarda cache para no repetir llamadas en futuras ejecuciones
    """)
