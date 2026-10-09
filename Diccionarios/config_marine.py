# =============================================================================
# config_marine.py
# Archivo centralizado de diccionarios para Marine.
# Todos los notebooks importan de aqui en lugar de definir diccionarios locales.
#
# USO EN CADA NOTEBOOK:
#   import sys
#   sys.path.insert(0, r"C:/Users/IKAL14/Documents/Integral/Marine")
#   from config_marine import *
# =============================================================================

# =============================================================================
# 1. COVER MAP: normaliza variantes de COVER a valores canonicos
# =============================================================================
COVER_MAP = {
    # CASCO Y MAQUINARIA
    'CASCO Y MAQ.'               : 'CASCO Y MAQ.',
    'CASCO Y MAQUINARIA'         : 'CASCO Y MAQ.',
    'CASCO'                      : 'CASCO Y MAQ.',
    'GASTOS DE SALVAMENTO'       : 'CASCO Y MAQ.',
    'DAÑOS A LA MAQUINARIA'      : 'CASCO Y MAQ.',
    # P&I
    'P&I'                        : 'P&I',
    'PANDI'                      : 'P&I',
    # CARGO (internacional)
    'Carga'                      : 'CARGO',
    'CARGO'                      : 'CARGO',
    'TRANSPORTE'                 : 'CARGO',
    'TRANSPORTE / CONTAMINACION' : 'CARGO',
    'TRANSPORTE/CONTAMINACION'   : 'CARGO',
    # CARGA
    'CARGA'                      : 'CARGO',
    'CARGA POLIETILENO'          : 'CARGA POLIETILENO',
    'POLIETILENO'                : 'CARGA POLIETILENO',
    # DEEP WATER
    'DEEP WATER'                : 'DEEP WATER',
    'DEEP WATERS'                : 'DEEP WATER',
    'AGUAS PROFUNDAS'            : 'DEEP WATER',
    # JACK-UPS
    'JACK-UPS'                   : 'JACK-UPS(DAÑO FISICO)',
    'JACK-UPS(DAÑO FISICO)'      : 'JACK-UPS(DAÑO FISICO)',  # identidad: sin esto el historico perdia la cobertura al normalizar (nb1, seccion 8)
    'JACK UPS'                   : 'JACK-UPS(DAÑO FISICO)',
    'PLATAFORMAS MOVILES'        : 'JACK-UPS(DAÑO FISICO)',
    # RC FLETADORES
    'RC FLETADORES'              : 'RC FLETADORES(PEMEX)',
    'FLETADORES PMI'             : 'RC FLETADORES(PMI)',
    'FLETADORESPMI'              : 'RC FLETADORES(PMI)',
    'FLETADORES RC PMI'          : 'RC FLETADORES(PMI)',
    'RC FLETADORES(PEMEX)'       : 'RC FLETADORES(PEMEX)',  # identidad (ver JACK-UPS)
    'RC FLETADORES(PMI)'         : 'RC FLETADORES(PMI)',    # identidad
    # EQUIPO FERROVIARIO
    'EQUIPO FERROVIARIO'         : 'EQUIPO FERROVIARIO(DAÑO FÍSICO)',
    'FERREO'                     : 'EQUIPO FERROVIARIO(DAÑO FÍSICO)',
    'EQUIPO FERROVIARIO(DAÑO FÍSICO)' : 'EQUIPO FERROVIARIO(DAÑO FÍSICO)',  # identidad
}

# =============================================================================
# 2. MAP LOB INWARD: COVER canonico -> LoB-Inward final
# =============================================================================
MAP_LOB_INWARD = {
    'CASCO Y MAQ.'                    : 'CASCO Y MAQ.',
    'CASCO Y MAQUINARIA'              : 'CASCO Y MAQ.',
    'GASTOS DE SALVAMENTO'            : 'CASCO Y MAQ.',
    'EQUIPO FERROVIARIO(DAÑO FÍSICO)' : 'EQUIPO FERROVIARIO(DAÑO FÍSICO)',
    'DEEP WATERS'                     : 'DEEP WATERS',
    'CARGA POLIETILENO'               : 'CARGO',
    'CARGA'                           : 'CARGO',
    'JACK-UPS(DAÑO FISICO)'           : 'JACK-UPS(DAÑO FISICO)',
    'CARGO'                           : 'CARGO',
    'P&I'                             : 'P&I',
    'PANDI'                           : 'P&I',
    'RC FLETADORES(PEMEX)'            : 'P&I',
    'RC FLETADORES(PMI)'              : 'P&I',
}

# =============================================================================
# 3. LOB NORMALIZE MAP: normaliza LoB de contabilidad (NB2, NB3)
# =============================================================================
LOB_NORMALIZE_MAP = {
    'cascoymaquinaria'   : 'CASCO Y MAQ.',
    'cascoy maquinaria'  : 'CASCO Y MAQ.',
    'casco y maquinaria' : 'CASCO Y MAQ.',
    'casco'              : 'CASCO Y MAQ.',
    'p&i'                : 'P&I',
    'pandi'              : 'P&I',
    'dw'                 : 'DEEP WATERS',
    'deep waters'        : 'DEEP WATERS',
    'deepwaters'         : 'DEEP WATERS',
    'cargo'              : 'CARGO',
    'plataformas'        : 'PLATAFORMAS',
    'floteles'           : 'FLOTELES',
}

# =============================================================================
# 4. COVER CONTABLE -> LOB INWARD (para NB3 validaciones)
# =============================================================================
COVER_CONTABLE_MAP = {
    'Casco'      : 'CASCO Y MAQ.',
    'Transporte' : 'CARGO',
    'Pandi'      : 'P&I',
    'Carga'      : 'CARGO',
}

# Casos especiales del cover contable (requieren poliza + cover)
COVER_CONTABLE_ESPECIAL = {
    ('3612100000008', 'Ferreo')                    : 'CARGA POLIETILENO',
    ('E01-2-60-000000010_0000-0-1', 'Ferreo')      : 'EQUIPO FERROVIARIO(DAÑO FÍSICO)',
}

# =============================================================================
# 5. POLIZAS SUBSIDIARIAS (se excluyen del proceso)
# =============================================================================
LIST_SUBSIDIARY = [
    '25300 30021823', '25200 30016456', '25200 30028005', '25300 30027961',
    '25300 30028201', '25300 30028443', '25300 30031974', '25200 30027587',
    'E01-2-71-000001094_0000-0-0', 'E01-2-71-1103'
]

# =============================================================================
# 6. POLIZAS LEGACY (sin nuevas entregas de BDX)
# =============================================================================
LIST_LEGACY = [
    'BJ200001', 'BJ2000120000', 'BJ2000120100', 'M9000325', 'M9000324',
    'CJ200025', 'BJ200008', 'CJ2000250100', 'CJ2000250200',
    '147736177', '38417374', '13637426', '90600 323484', '90600 328256', 'M9000324',
    'M9000325',
    '90600 320575',  # poliza 2004 sin BDX; la manual la conserva congelada (agregada oct-2026)
    '25300 30014476'  # poliza 2014 con un solo siniestro (35100 3070073, deducible 5M) que ningun BDX reporta; congelada como legacy (agregada oct-2026)
]

# =============================================================================
# 7. PERIODOS DE POLIZA (inicio y fin)
# =============================================================================
DICT_POLICY_START = {
    'M9000325': '30/06/1999',
    'M9000324': '30/06/1999',
    'CJ200025': '30/06/2002',
    'BJ200008': '30/06/2002',
    'CJ2000250200': '30/06/2004',
    '90600 00320575': '30/06/2004',
    '90600 323484': '03/05/2005',
    '90600 328256': '20/02/2007',
    '25200 30002933': '20/02/2009',
    '25200 30006350': '20/02/2011',
    '25200 30008857': '31/08/2012',
    '25300 30011610': '20/02/2013',
    '147736177': '20/02/2015',
    'NCGL-070-1000773': '20/02/2017',
    'E01-2-60-000000003_0000-0-1': '20/02/2019',
    '3612100000008': '20/02/2021',
    'E01-2-60-000000010_0000-0-1': '20/04/2023',
    'NCGL-070-1002258': '20/02/2025',
    '25300 30014476': '20/02/2014',  # Jack Ups INBURSA 2014-2016 (catalogo de polizas)
}

DICT_POLICY_END = {
    'M9000325': '30/06/2002',
    'M9000324': '30/06/2002',
    'CJ200025': '30/06/2003',
    'BJ200008': '30/06/2003',
    'CJ2000250200': '30/06/2005',
    '90600 00320575': '30/06/2005',
    '90600 323484': '20/02/2007',
    '90600 328256': '20/02/2009',
    '25200 30002933': '20/02/2011',
    '25200 30006350': '20/02/2013',
    '25200 30008857': '31/12/2014',
    '25300 30011610': '20/02/2015',
    '147736177': '20/02/2017',
    'NCGL-070-1000773': '20/02/2019',
    'E01-2-60-000000003_0000-0-1': '20/02/2021',
    '3612100000008': '20/04/2023',
    'E01-2-60-000000010_0000-0-1': '20/02/2025',
    'NCGL-070-1002258': '20/02/2027',
    '25300 30014476': '20/02/2016',  # Jack Ups INBURSA 2014-2016 (catalogo de polizas)
}

# =============================================================================
# 7b. CORRECCIONES DE VIGENCIA SOBRE EL HISTORICO
# =============================================================================
# Las filas legacy se congelan tal como vienen de la base del mes anterior, asi que una
# vigencia mal cargada se arrastraria para siempre. El notebook 1 aplica estas correcciones
# al cargar esa base (seccion 8). Formato: poliza -> {columna: fecha ISO}.
CORRECCIONES_VIGENCIA_POLIZA = {
    # Catalogo de polizas: '05-Jack-Ups', 20/02/2014 a 20/02/2016, 'Jack Ups INBURSA 2014-2016'.
    # La base heredada traia el fin en 20/02/2015.
    '25300 30014476': {'POLICY PERIOD START DATE': '2014-02-20', 'POLICY PERIOD END DATE': '2016-02-20'},
}

# =============================================================================
# 8. SUBSIDIARIAS ETILENO (para reclasificacion CARGA -> CARGA POLIETILENO)
# =============================================================================
SUBSIDIARIAS_POLIETILENO = {'ETILENO', 'PEMEX ETILENO'}

# =============================================================================
# 9. SUBSIDIARIAS DE FERROCARRIL (para validacion de hojas Ferreo)
# =============================================================================
SUBSIDIARIAS_FERREO = {"'ETILENO", 'ETILENO', 'PEMEX ETILENO'}

# =============================================================================
# 10. NORMALIZACION DE SUBSIDIARIAS PEMEX
# =============================================================================
DICT_SUBSIDIARIES = {
    'PEMEX Logistica' : 'LOGÍSTICA',
    'LOGISTICA'       : 'LOGÍSTICA',
    'Logistica'       : 'LOGÍSTICA',
    'Pemex Logística' : 'LOGÍSTICA',
    'LOG'             : 'LOGÍSTICA',
}

# =============================================================================
# 11. STATUS VALIDOS
# =============================================================================
VALID_STATUSES = {'P', 'C', 'T'}

# =============================================================================
# 12. VALORES VACIOS ESTANDAR
# =============================================================================
VALORES_VACIOS = ['', 'NAN', 'NO ESPECIFICADO', 'N/A', 'NONE', '-', '.']

# =============================================================================
# 13. RUTAS BASE (ajustar si cambia el usuario o equipo)
# =============================================================================
import os

DIRECTORIO_PROYECTO = os.environ.get(
    'MARINE_BASE_DIR',
    'C:/Users/IKAL14/Documents/Integral/Marine'
)
RUTA_INSUMOS = os.environ.get(
    'MARINE_INSUMOS',
    'C:/Users/IKAL14/Documents/Integral/Insumos'
)
RUTA_CONTABILIDAD = f'{RUTA_INSUMOS}/Contabilidad'
RUTA_ONEDRIVE = os.environ.get(
    'MARINE_ONEDRIVE',
    'C:/Users/IKAL14/OneDrive - Kot Insurance Company AG/Transporte, Carga y Embarcaciones'
)


# =============================================================================
# FUNCIONES UTILITARIAS COMPARTIDAS
# =============================================================================

def get_rutas(AñoMes):
    """Genera todas las rutas derivadas del periodo."""
    return {
        'procesados'   : f'{DIRECTORIO_PROYECTO}/Procesados/{AñoMes}',
        'incidencias'  : f'{DIRECTORIO_PROYECTO}/Incidencias/{AñoMes}',
        'validaciones' : f'{DIRECTORIO_PROYECTO}/Validaciones/{AñoMes}',
        'catalogos'    : f'{DIRECTORIO_PROYECTO}/Catalogos',
        'bases'        : f'{DIRECTORIO_PROYECTO}/Bases',
        'contabilidad' : f'{RUTA_CONTABILIDAD}/{AñoMes}',
    }


def normalizar_lob_contable(lob_raw):
    """Normaliza LoB de archivos contables a formato canonico."""
    if not isinstance(lob_raw, str):
        return lob_raw
    key = lob_raw.strip().lower().replace(' ', '')
    # Buscar en el mapa (probamos con y sin espacios)
    for k, v in LOB_NORMALIZE_MAP.items():
        if key == k.replace(' ', ''):
            return v
    return lob_raw


def map_cover_to_lob(cover_text):
    """Mapea COVER canonico a LoB-Inward."""
    if not isinstance(cover_text, str):
        return cover_text
    cleaned = cover_text.strip().upper()
    return COVER_MAP.get(cleaned, cleaned)


# =============================================================================
# 14. OSLR - AJUSTES MANUALES Y UMBRALES
# =============================================================================

# Umbral minimo de OSLR: por debajo de este monto, se zerea (ruido / redondeo)
UMBRAL_OSLR_MINIMO = 100

# Claims zereados manualmente en OSLR Inward, con vigencia: el valor es el
# ultimo AñoMes (YYYYMM) en el que el zereo debe seguir aplicandose. Al
# procesar un periodo posterior a la vigencia, el claim deja de zerearse
# automaticamente y hay que revisar si el ajuste sigue siendo necesario.
OSLR_ZERO_MANUAL = {
    '4431/2023' : 202509,
    '1560/2024' : 202509,
    '1563/2024' : 202509,
    '4478/2024' : 202509,
    '4801/2024' : 202509,
    '4803/2024' : 202509,
    '5704/2024' : 202509,
    '6399/2024' : 202509,
    '6400/2024' : 202509,
    '161/2025'  : 202509,
    '594/2025'  : 202509,
}

# Claims a verificar/loguear tras aplicar el fallback de GROSS RESERVE/DEDUCTIBLE
# (Section 5.5) — util para dar seguimiento a casos puntuales mes a mes.
SINIESTROS_VERIFICAR = ['324372640000425', '324372640000403']


def claims_oslr_zero_vigentes(AñoMes):
    """Devuelve los claims cuyo zereo manual de OSLR sigue vigente para AñoMes."""
    return [claim for claim, periodo_hasta in OSLR_ZERO_MANUAL.items() if AñoMes <= periodo_hasta]


# =============================================================================
# 15. CONSOLIDACION DE COLUMNAS TRAS MERGE (_x/_y/_old/_new)
# =============================================================================

def consolidar_columna(df, base):
    """
    Consolida las variantes de una columna que quedan tras un merge
    (base_old/base_new o base_x/base_y) en una sola columna `base`,
    priorizando la version mas reciente (new/x) y usando la anterior
    (old/y) para rellenar los nulos. Tolera re-ejecuciones fuera de orden:
    si `base` ya existe sin sufijos, no hace nada.
    """
    for suf_new, suf_old in [('_new', '_old'), ('_x', '_y')]:
        col_new, col_old = f'{base}{suf_new}', f'{base}{suf_old}'
        if col_new in df.columns and col_old in df.columns:
            df[base] = df[col_new].fillna(df[col_old])
            df.drop(columns=[col_new, col_old], inplace=True)
        elif col_new in df.columns:
            df.rename(columns={col_new: base}, inplace=True)
        elif col_old in df.columns:
            df.rename(columns={col_old: base}, inplace=True)
    return df


# =============================================================================
# 8. GUARDIA DE REFERENCIA LEGACY (base fija 202509 MANUAL)
# =============================================================================
# Las polizas legacy no reciben BDX nuevo, asi que su Reserva Bruta y Deducible
# NO deben cambiar entre meses. Las guardias de los notebooks 1 y 2 solo comparan
# contra la base del mes anterior; si esa base ya venia alterada el error se
# propaga sin que nadie lo vea. Esta guardia compara contra una foto FIJA:
# REF_LEGACY_202509.xlsx = filas legacy de
# 'DB MANUAL/202509_Siniestros_Marine_MANUAL.xlsx' (952 filas con LIST_LEGACY actual; 951 hasta incluir '25300 30014476'; 938 hasta incluir '90600 320575').
# Si se agrega una poliza a LIST_LEGACY o se corrige la referencia a proposito,
# regenerar este archivo.
REF_LEGACY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'REF_LEGACY_202509.xlsx')
GUARDIA_REF_ESTRICTA = True  # True: detiene el proceso si legacy difiere; False: solo advierte


def _normalizar_claim(x):
    # Sin espacios: el notebook 1 (Seccion 3) los quita de CLAIM NUMBER en la base de partida
    # (conserva el original en 'CLAIM NUMBER ORIGINAL'), pero la referencia y el export los traen.
    s = ''.join(str(x).split())
    return s[:-2] if s.endswith('.0') else s


def _huella_legacy(df):
    """Multiconjunto (poliza, claim, reserva bruta, deducible) de las filas legacy de df.
    Los montos se redondean a unidades para ignorar ruido de punto flotante de Excel."""
    from collections import Counter
    import pandas as pd
    legacy = {str(p).strip() for p in LIST_LEGACY}
    pol = df['INWARD POLICY N°'].astype(str).str.strip()
    sub = df.loc[pol.isin(legacy)]
    pol = pol.loc[sub.index]
    gross = pd.to_numeric(sub['GROSS RESERVE'], errors='coerce').fillna(0).round(0)
    ded = pd.to_numeric(sub['DEDUCTIBLE'], errors='coerce').fillna(0).round(0)
    claim = sub['CLAIM NUMBER'].map(_normalizar_claim)
    return Counter(zip(pol, claim, gross, ded))


def verificar_legacy_vs_referencia(df, etapa, estricta=None):
    """Compara las filas legacy de df contra REF_LEGACY_202509.xlsx.

    Mira fila por fila (poliza, claim, GROSS RESERVE, DEDUCTIBLE); los pagos y el
    OSLR no se comparan porque los pagos si pueden moverse en legacy. Si hay
    diferencias imprime un resumen por poliza y, con estricta=True, lanza ValueError.
    Requiere en df: 'INWARD POLICY N°', 'CLAIM NUMBER', 'GROSS RESERVE', 'DEDUCTIBLE'.
    """
    import pandas as pd
    if estricta is None:
        estricta = GUARDIA_REF_ESTRICTA
    ref = pd.read_excel(REF_LEGACY_PATH, dtype={'CLAIM NUMBER': str})
    h_ref, h_df = _huella_legacy(ref), _huella_legacy(df)
    solo_ref, solo_df = h_ref - h_df, h_df - h_ref
    n_ref = sum(h_ref.values())
    if not solo_ref and not solo_df:
        print(f'\u2705 Guardia legacy vs referencia 202509 [{etapa}]: {n_ref} filas legacy identicas a la referencia.')
        return True
    resumen = {}
    for (pol, *_), n in solo_ref.items():
        resumen.setdefault(pol, [0, 0])[0] += n
    for (pol, *_), n in solo_df.items():
        resumen.setdefault(pol, [0, 0])[1] += n
    lineas = [f'  {pol}: {a} fila(s) de la referencia sin igual en la base, {b} fila(s) de la base sin igual en la referencia'
              for pol, (a, b) in sorted(resumen.items())]
    ejemplos = [f'    REF  {k}' for k in list(solo_ref)[:5]] + [f'    BASE {k}' for k in list(solo_df)[:5]]
    msg = (f'GUARDIA LEGACY vs REFERENCIA 202509 [{etapa}]: la info legacy NO coincide con la referencia '
           f'({sum(solo_ref.values())} de {n_ref} filas de la referencia difieren).\n'
           + '\n'.join(lineas) + '\n  Ejemplos (poliza, claim, reserva bruta, deducible):\n' + '\n'.join(ejemplos))
    if estricta:
        raise ValueError(msg)
    print('\u26a0\ufe0f ' + msg)
    return False
