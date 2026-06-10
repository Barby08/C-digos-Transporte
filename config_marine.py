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
    'CARGO'                      : 'CARGO',
    'TRANSPORTE'                 : 'CARGO',
    'TRANSPORTE / CONTAMINACION' : 'CARGO',
    'TRANSPORTE/CONTAMINACION'   : 'CARGO',
    # CARGA
    'CARGA'                      : 'CARGA',
    'CARGA POLIETILENO'          : 'CARGA POLIETILENO',
    'POLIETILENO'                : 'CARGA POLIETILENO',
    # DEEP WATERS
    'DEEP WATERS'                : 'DEEP WATERS',
    'AGUAS PROFUNDAS'            : 'DEEP WATERS',
    # JACK-UPS
    'JACK-UPS'                   : 'JACK-UPS(DAÑO FISICO)',
    'JACK UPS'                   : 'JACK-UPS(DAÑO FISICO)',
    'PLATAFORMAS MOVILES'        : 'JACK-UPS(DAÑO FISICO)',
    # RC FLETADORES
    'RC FLETADORES'              : 'RC FLETADORES(PEMEX)',
    'FLETADORES PMI'             : 'RC FLETADORES(PMI)',
    'FLETADORESPMI'              : 'RC FLETADORES(PMI)',
    'FLETADORES RC PMI'          : 'RC FLETADORES(PMI)',
    # EQUIPO FERROVIARIO
    'EQUIPO FERROVIARIO'         : 'EQUIPO FERROVIARIO(DAÑO FÍSICO)',
    'FERREO'                     : 'EQUIPO FERROVIARIO(DAÑO FÍSICO)',
}

# =============================================================================
# 2. MAP LOB INWARD: COVER canonico -> LoB-Inward final
# =============================================================================
MAP_LOB_INWARD = {
    'CASCO Y MAQ.'                    : 'CASCO Y MAQ.',
    'GASTOS DE SALVAMENTO'            : 'CASCO Y MAQ.',
    'EQUIPO FERROVIARIO(DAÑO FÍSICO)' : 'EQUIPO FERROVIARIO(DAÑO FÍSICO)',
    'DEEP WATERS'                     : 'DEEP WATERS',
    'CARGA'                           : 'CARGA',
    'CARGA POLIETILENO'               : 'CARGA',
    'JACK-UPS(DAÑO FISICO)'           : 'JACK-UPS(DAÑO FISICO)',
    'CARGO'                           : 'CARGO',
    'P&I'                             : 'P&I',
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
    'Carga'      : 'CARGA',
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
    '25300 30028201', '25300 30028443', '25300 30031974', '25200 30027587'
]

# =============================================================================
# 6. POLIZAS LEGACY (sin nuevas entregas de BDX)
# =============================================================================
LIST_LEGACY = [
    'BJ200001', 'BJ2000120000', 'BJ2000120100', 'M9000325', 'M9000324',
    'CJ200025', 'BJ200008', 'CJ2000250100', 'CJ2000250200',
    '147736177', '38417374', '13637426',
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
    'E01-2-60-000000010_0000-0-1': '20/02/2023',
    'NCGL-070-1002258': '20/02/2025',
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
    '3612100000008': '20/02/2023',
    'E01-2-60-000000010_0000-0-1': '20/02/2025',
    'NCGL-070-1002258': '20/02/2027',
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
