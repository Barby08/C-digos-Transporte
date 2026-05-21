"""
OPCION 1 - Clasificador OFFLINE de Estado por LOCATION
Sin APIs externas. Usa catalogos locales + heuristicas de texto.
Dependencias: pandas, unidecode, re

Como funciona (pipeline de 6 etapas):
  1. Normaliza el texto (mayusculas, sin acentos, sin puntuacion)
  2. Detecta ubicaciones internacionales -> "USA", "PANAMA", etc.
  3. Busca estados escritos completos en el texto
  4. Busca abreviaturas de estados (NL, QRO, VER, etc.)
  5. Busca municipios/ciudades conocidas y devuelve su estado
  6. Si nada matchea -> "NO IDENTIFICADO"

Ventajas:
  - No requiere internet ni API keys
  - Rapido (~1 seg para 10K filas)
  - 100% reproducible
  - Facil de extender agregando entradas al catalogo

Desventajas:
  - No cubre TODOS los municipios posibles (solo los del catalogo)
  - No resuelve coordenadas geograficas
"""

import pandas as pd
import re
from unidecode import unidecode
from collections import OrderedDict

# ============================================================
# CATALOGO 1: Estados de Mexico (nombre limpio -> nombre oficial)
# ============================================================
ESTADOS_MX = OrderedDict([
    ("BAJA CALIFORNIA SUR",   "BAJA CALIFORNIA SUR"),
    ("QUINTANA ROO",          "QUINTANA ROO"),
    ("SAN LUIS POTOSI",       "SAN LUIS POTOSI"),
    ("CIUDAD DE MEXICO",      "CIUDAD DE MEXICO"),
    ("ESTADO DE MEXICO",      "ESTADO DE MEXICO"),
    ("BAJA CALIFORNIA",       "BAJA CALIFORNIA"),
    ("NUEVO LEON",            "NUEVO LEON"),
    ("AGUASCALIENTES",        "AGUASCALIENTES"),
    ("CAMPECHE",              "CAMPECHE"),
    ("CHIAPAS",               "CHIAPAS"),
    ("CHIHUAHUA",             "CHIHUAHUA"),
    ("COAHUILA",              "COAHUILA"),
    ("COLIMA",                "COLIMA"),
    ("DURANGO",               "DURANGO"),
    ("GUANAJUATO",            "GUANAJUATO"),
    ("GUERRERO",              "GUERRERO"),
    ("HIDALGO",               "HIDALGO"),
    ("JALISCO",               "JALISCO"),
    ("MICHOACAN",             "MICHOACAN"),
    ("MORELOS",               "MORELOS"),
    ("NAYARIT",               "NAYARIT"),
    ("OAXACA",                "OAXACA"),
    ("PUEBLA",                "PUEBLA"),
    ("QUERETARO",             "QUERETARO"),
    ("SINALOA",               "SINALOA"),
    ("SONORA",                "SONORA"),
    ("TABASCO",               "TABASCO"),
    ("TAMAULIPAS",            "TAMAULIPAS"),
    ("TLAXCALA",              "TLAXCALA"),
    ("VERACRUZ",              "VERACRUZ"),
    ("YUCATAN",               "YUCATAN"),
    ("ZACATECAS",             "ZACATECAS"),
])

# ============================================================
# CATALOGO 2: Abreviaturas -> Estado oficial
# ============================================================
ABREVIATURAS = {
    "AGS":            "AGUASCALIENTES",
    "BC":             "BAJA CALIFORNIA",
    "B.C":            "BAJA CALIFORNIA",
    "B.C.":           "BAJA CALIFORNIA",
    "BCS":            "BAJA CALIFORNIA SUR",
    "B.C.S":          "BAJA CALIFORNIA SUR",
    "CAMP":           "CAMPECHE",
    "CHIS":           "CHIAPAS",
    "CHIH":           "CHIHUAHUA",
    "COAH":           "COAHUILA",
    "COL":            "COLIMA",
    "CDMX":           "CIUDAD DE MEXICO",
    "D.F.":           "CIUDAD DE MEXICO",
    "D.F":            "CIUDAD DE MEXICO",
    "DF":             "CIUDAD DE MEXICO",
    "DGO":            "DURANGO",
    "GTO":            "GUANAJUATO",
    "GRO":            "GUERRERO",
    "HGO":            "HIDALGO",
    "JAL":            "JALISCO",
    "MEX":            "ESTADO DE MEXICO",
    "EDOMEX":         "ESTADO DE MEXICO",
    "EDO MEX":        "ESTADO DE MEXICO",
    "EDO. MEX":       "ESTADO DE MEXICO",
    "EDO DE MEX":     "ESTADO DE MEXICO",
    "EDO. DE MEX":    "ESTADO DE MEXICO",
    "EDO DE MEXICO":  "ESTADO DE MEXICO",
    "EDO. DE MEXICO": "ESTADO DE MEXICO",
    "EDO. MEXICO":    "ESTADO DE MEXICO",
    "MICH":           "MICHOACAN",
    "MOR":            "MORELOS",
    "NAY":            "NAYARIT",
    "NL":             "NUEVO LEON",
    "NL.":            "NUEVO LEON",
    "N.L":            "NUEVO LEON",
    "N.L.":           "NUEVO LEON",
    "OAX":            "OAXACA",
    "PUE":            "PUEBLA",
    "QRO":            "QUERETARO",
    "Q. ROO":         "QUINTANA ROO",
    "QROO":           "QUINTANA ROO",
    "Q.ROO":          "QUINTANA ROO",
    "SLP":            "SAN LUIS POTOSI",
    "SIN":            "SINALOA",
    "SON":            "SONORA",
    "TAB":            "TABASCO",
    "TAM":            "TAMAULIPAS",
    "TAMPS":          "TAMAULIPAS",
    "TLAX":           "TLAXCALA",
    "VER":            "VERACRUZ",
    "VER.":           "VERACRUZ",
    "VERACRZ":        "VERACRUZ",
    "YUC":            "YUCATAN",
    "ZAC":            "ZACATECAS",
}

# ============================================================
# CATALOGO 3: Ciudades/Municipios principales -> Estado
# ============================================================
CIUDADES = {
    # Tamaulipas
    "CIUDAD MADERO":      "TAMAULIPAS",
    "CD MADERO":          "TAMAULIPAS",
    "CD. MADERO":         "TAMAULIPAS",
    "ALTAMIRA":           "TAMAULIPAS",
    "TAMPICO":            "TAMAULIPAS",
    "REYNOSA":            "TAMAULIPAS",
    "MATAMOROS":          "TAMAULIPAS",
    "CIUDAD VICTORIA":    "TAMAULIPAS",
    "CD VICTORIA":        "TAMAULIPAS",
    "CD. VICTORIA":       "TAMAULIPAS",
    "NUEVO LAREDO":       "TAMAULIPAS",
    "MANTE":              "TAMAULIPAS",
    "CIUDAD MANTE":       "TAMAULIPAS",
    # Veracruz
    "COATZACOALCOS":      "VERACRUZ",
    "MINATITLAN":         "VERACRUZ",
    "POZA RICA":          "VERACRUZ",
    "TUXPAN":             "VERACRUZ",
    "CORDOBA":            "VERACRUZ",
    "ORIZABA":            "VERACRUZ",
    "XALAPA":             "VERACRUZ",
    "COSOLEACAQUE":       "VERACRUZ",
    "COSAMALOAPAN":       "VERACRUZ",
    "ACAYUCAN":           "VERACRUZ",
    "NANCHITAL":          "VERACRUZ",
    "LAS CHOAPAS":        "VERACRUZ",
    "MARTINEZ DE LA TORRE":"VERACRUZ",
    "PEROTE":             "VERACRUZ",
    "TIERRA BLANCA":      "VERACRUZ",
    "COTAXTLA":           "VERACRUZ",
    "PAJARITOS":          "VERACRUZ",
    "TAD PAJARITOS":      "VERACRUZ",
    "PUERTO DE VERACRUZ": "VERACRUZ",
    # Nuevo Leon
    "MONTERREY":          "NUEVO LEON",
    "APODACA":            "NUEVO LEON",
    "CADEREYTA":          "NUEVO LEON",
    "GARCIA":             "NUEVO LEON",
    "GUADALUPE":          "NUEVO LEON",
    "SAN PEDRO GARZA GARCIA":"NUEVO LEON",
    "SAN NICOLAS DE LOS GARZA":"NUEVO LEON",
    "SANTA CATARINA":     "NUEVO LEON",
    "LINARES":            "NUEVO LEON",
    "CIENEGA DE FLORES":  "NUEVO LEON",
    # CDMX
    "AZCAPOTZALCO":       "CIUDAD DE MEXICO",
    "IZTAPALAPA":         "CIUDAD DE MEXICO",
    "GUSTAVO A. MADERO":  "CIUDAD DE MEXICO",
    "TLALPAN":            "CIUDAD DE MEXICO",
    "COYOACAN":           "CIUDAD DE MEXICO",
    "XOCHIMILCO":         "CIUDAD DE MEXICO",
    "CUAJIMALPA":         "CIUDAD DE MEXICO",
    "ALVARO OBREGON":     "CIUDAD DE MEXICO",
    "MIGUEL HIDALGO":     "CIUDAD DE MEXICO",
    # Estado de Mexico
    "TOLUCA":             "ESTADO DE MEXICO",
    "ECATEPEC":           "ESTADO DE MEXICO",
    "NAUCALPAN":          "ESTADO DE MEXICO",
    "TLALNEPANTLA":       "ESTADO DE MEXICO",
    "ATIZAPAN":           "ESTADO DE MEXICO",
    "CUAUTITLAN":         "ESTADO DE MEXICO",
    "CUAUTITLAN IZCALLI": "ESTADO DE MEXICO",
    "TEPOTZOTLAN":        "ESTADO DE MEXICO",
    "TULTITLAN":          "ESTADO DE MEXICO",
    "COYOTEPEC":          "ESTADO DE MEXICO",
    "POLOTITLAN":         "ESTADO DE MEXICO",
    "ATLACOMULCO":        "ESTADO DE MEXICO",
    "ACAMBAY":            "ESTADO DE MEXICO",
    "JILOTEPEC":          "ESTADO DE MEXICO",
    "TEPALTITLAN":        "ESTADO DE MEXICO",
    "LERMA":              "ESTADO DE MEXICO",
    "NOPALTEPEC":         "ESTADO DE MEXICO",
    # Campeche
    "CIUDAD DEL CARMEN":  "CAMPECHE",
    "CD. DEL CARMEN":     "CAMPECHE",
    "CD DEL CARMEN":      "CAMPECHE",
    "CARMEN":             "CAMPECHE",
    "CALKINI":            "CAMPECHE",
    "PUERTO DE LERMA":    "CAMPECHE",
    # Tabasco
    "VILLAHERMOSA":       "TABASCO",
    "CARDENAS":           "TABASCO",
    "CUNDUACAN":          "TABASCO",
    "CENTRO":             "TABASCO",
    "PARAISO":            "TABASCO",
    "DOS BOCAS":          "TABASCO",
    # Jalisco
    "GUADALAJARA":        "JALISCO",
    "ZAPOPAN":            "JALISCO",
    "TLAQUEPAQUE":        "JALISCO",
    "PUERTO VALLARTA":    "JALISCO",
    "CD GUZMAN":          "JALISCO",
    "LAGOS DE MORENO":    "JALISCO",
    "ENCARNACION DIAZ":   "JALISCO",
    # Guanajuato
    "LEON":               "GUANAJUATO",
    "CELAYA":             "GUANAJUATO",
    "IRAPUATO":           "GUANAJUATO",
    "SALAMANCA":          "GUANAJUATO",
    "SILAO":              "GUANAJUATO",
    "APASEO EL GRANDE":   "GUANAJUATO",
    "SAN JOSE DE ITURBIDE":"GUANAJUATO",
    # Guerrero
    "ACAPULCO":           "GUERRERO",
    "ZIHUATANEJO":        "GUERRERO",
    "CHILPANCINGO":       "GUERRERO",
    "IGUALA":             "GUERRERO",
    "TAXCO":              "GUERRERO",
    # Puebla
    "TEZIUTLAN":          "PUEBLA",
    "TEHUACAN":           "PUEBLA",
    "ATLIXCO":            "PUEBLA",
    "ACTAZINGO":          "PUEBLA",
    "SAN MARTIN TEXMELUCAN":"PUEBLA",
    # Queretaro
    "SANTIAGO DE QUERETARO":"QUERETARO",
    "SAN JUAN DEL RIO":   "QUERETARO",
    "PALMILLAS":          "QUERETARO",
    # Hidalgo
    "PACHUCA":            "HIDALGO",
    "TULA DE ALLENDE":    "HIDALGO",
    "TULA":               "HIDALGO",
    "ACTOPAN":            "HIDALGO",
    "SINGUILUCAN":        "HIDALGO",
    "SAN JUAN MICHIMALOYA":"HIDALGO",
    # Coahuila
    "SALTILLO":           "COAHUILA",
    "TORREON":            "COAHUILA",
    "MONCLOVA":           "COAHUILA",
    "PIEDRAS NEGRAS":     "COAHUILA",
    "RAMOS ARIZPE":       "COAHUILA",
    # San Luis Potosi
    "SAN LUIS POTOSI":    "SAN LUIS POTOSI",
    "MATEHUALA":          "SAN LUIS POTOSI",
    "CIUDAD VALLES":      "SAN LUIS POTOSI",
    "CD DEL MAIZ":        "SAN LUIS POTOSI",
    # Oaxaca
    "SALINA CRUZ":        "OAXACA",
    "JUCHITAN":           "OAXACA",
    "IXTEPEC":            "OAXACA",
    "TEHUANTEPEC":        "OAXACA",
    "MATIAS ROMERO":      "OAXACA",
    # Sinaloa
    "MAZATLAN":           "SINALOA",
    "CULIACAN":           "SINALOA",
    "LOS MOCHIS":         "SINALOA",
    "AHOME":              "SINALOA",
    "NAVOLATO":           "SINALOA",
    "CONCORDIA":          "SINALOA",
    "TOPOLOBAMPO":        "SINALOA",
    # Sonora
    "HERMOSILLO":         "SONORA",
    "CAJEME":             "SONORA",
    "CIUDAD OBREGON":     "SONORA",
    "GUAYMAS":            "SONORA",
    "NOGALES":            "SONORA",
    "EMPALME":            "SONORA",
    "CANANEA":            "SONORA",
    "NAVOJOA":            "SONORA",
    "IMURIS":             "SONORA",
    "AGUA PRIETA":        "SONORA",
    # Chihuahua
    "CIUDAD JUAREZ":      "CHIHUAHUA",
    "DELICIAS":           "CHIHUAHUA",
    "CUAUHTEMOC":         "CHIHUAHUA",
    "JIMENEZ":            "CHIHUAHUA",
    "CAMARGO":            "CHIHUAHUA",
    "PARRAL":             "CHIHUAHUA",
    # Chiapas
    "TUXTLA GUTIERREZ":   "CHIAPAS",
    "TAPACHULA":          "CHIAPAS",
    "ARRIAGA":            "CHIAPAS",
    "OCOZOCOAUTLA":       "CHIAPAS",
    "OCOZOCUAUTLA":       "CHIAPAS",
    # Morelos
    "CUERNAVACA":         "MORELOS",
    "CUAUTLA":            "MORELOS",
    # Yucatan
    "MERIDA":             "YUCATAN",
    "PROGRESO":           "YUCATAN",
    # Quintana Roo
    "CANCUN":             "QUINTANA ROO",
    "PLAYA DEL CARMEN":   "QUINTANA ROO",
    "CHETUMAL":           "QUINTANA ROO",
    # Baja California
    "TIJUANA":            "BAJA CALIFORNIA",
    "MEXICALI":           "BAJA CALIFORNIA",
    "ENSENADA":           "BAJA CALIFORNIA",
    "TECATE":             "BAJA CALIFORNIA",
    "LA RUMOROSA":        "BAJA CALIFORNIA",
    "ROSARITO":           "BAJA CALIFORNIA",
    # Baja California Sur
    "SAN JOSE DEL CABO":  "BAJA CALIFORNIA SUR",
    # Durango
    "LERDO":              "DURANGO",
    "GOMEZ PALACIO":      "DURANGO",
    "AGUILERA":           "DURANGO",
    "VICENTE GUERRERO":   "DURANGO",
    # Michoacan
    "LAZARO CARDENAS":    "MICHOACAN",
    "URUAPAN":            "MICHOACAN",
    "PATZCUARO":          "MICHOACAN",
    "COPANDARO DE GALEANA":"MICHOACAN",
    "COPANDARO":          "MICHOACAN",
    "CUITZEO":            "MICHOACAN",
    "NUEVA ITALIA":       "MICHOACAN",
    # Otros
    "SAYULA DE ALEMAN":   "VERACRUZ",
    "TEPIC":              "NAYARIT",
    "CALPULALPAN":        "TLAXCALA",
    "CONCEPCION DEL ORO": "ZACATECAS",
    "FRESNILLO":          "ZACATECAS",
    "COSIO":              "AGUASCALIENTES",
    "COLON":              "QUERETARO",
    # Terminales TAD/TAR/TASP (infraestructura PEMEX)
    "TAD MADERO":         "TAMAULIPAS",
    "TAR MADERO":         "TAMAULIPAS",
    "TASP MADERO":        "TAMAULIPAS",
    "TERMINAL MADERO":    "TAMAULIPAS",
    "TERMINAL MARITIMA MADERO": "TAMAULIPAS",
    "TAD 18 DE MARZO":    "CIUDAD DE MEXICO",
    "TAD 18 MARZO":       "CIUDAD DE MEXICO",
    "TAD TEPEIXTLES":     "COLIMA",
    "TAR TEPEIXTLES":     "COLIMA",
    "TAR DE TEPEIXTLES":  "COLIMA",
    "TAD EL CASTILLO":    "JALISCO",
    "TAD CASTILLO":       "JALISCO",
    "TAR EL CASTILLO":    "JALISCO",
    "TAD TOPOLOBAMPO":    "SINALOA",
    "TAD LA PAZ":         "BAJA CALIFORNIA SUR",
    "TAR DE LA PAZ":      "BAJA CALIFORNIA SUR",
    "TAD BAJOS DE LA GALLEGA": "VERACRUZ",
    "CE BAJOS DE LA GALLEGA":  "VERACRUZ",
    "C.E.BAJOS DE LA GALLEGA": "VERACRUZ",
    "BAJOS DE LA GALLEGA":     "VERACRUZ",
    "TAD ANIL":           "VERACRUZ",
    "TAR ROSARITO":       "BAJA CALIFORNIA",
    "TAR MAGDALENA":      "SONORA",
    "TAR DE MAGDALENA":   "SONORA",
    "TAD ZAMORA":         "MICHOACAN",
    "TAR DE ZAMORA":      "MICHOACAN",
    "TAR MANZANILLO":     "COLIMA",
    "MANZANILLO":         "COLIMA",
    "TAD STA. CATARINA":  "NUEVO LEON",
    "MADERO":             "TAMAULIPAS",
}

# ============================================================
# CATALOGO 4: Ubicaciones internacionales
# ============================================================
INTERNACIONAL_KEYWORDS = {
    "USA":           "USA",
    "EUA":           "USA",
    "EEUU":          "USA",
    "UNITED STATES": "USA",
    "TEXAS":         "USA",
    "HOUSTON":       "USA",
    "GALVESTON":     "USA",
    "BEAUMONT":      "USA",
    "PORT ARTHUR":   "USA",
    "PORT ARTUR":    "USA",
    "CALIFORNIA":    "USA",
    "LAKE CHARLES":  "USA",
    "SAN FRANCISCO": "USA",
    "NUEVA JERSEY":  "USA",
    "NEW JERSEY":    "USA",
    "LOUISIANA":     "USA",
    "PASADENA":      "USA",
    "SAN DIEGO":     "USA",
    "PANAMA":        "PANAMA",
    "BALBOA":        "PANAMA",
    "CHILE":         "CHILE",
    "TALCAHUANO":    "CHILE",
    "ALEMANIA":      "ALEMANIA",
    "SINGAPORE":     "SINGAPUR",
    "AMSTERDAM":     "PAISES BAJOS",
    "REGION MARINA":  "GOLFO DE MEXICO (MAR)",
    "GOLFO DE MEXICO":"GOLFO DE MEXICO (MAR)",
    "AGUAS DEL GOLFO":"GOLFO DE MEXICO (MAR)",
    "BAHIA DE CAMPECHE":"GOLFO DE MEXICO (MAR)",
    "NOHOCH":         "GOLFO DE MEXICO (MAR)",
    "CANTARELL":      "GOLFO DE MEXICO (MAR)",
}

# ============================================================
# CATALOGO 5: Autopistas/Rutas conocidas -> Estado probable
# ============================================================
AUTOPISTAS = {
    "MEX-QRO":                     "QUERETARO",
    "MEXICO-QUERETARO":            "QUERETARO",
    "MEXICO QRO":                  "QUERETARO",
    "ARCO NORTE":                  "HIDALGO",
    "CORDOBA-VERACRUZ":            "VERACRUZ",
    "CORDOBA-PUEBLA":              "VERACRUZ",
    "COATZACOALCOS-VILLAHERMOSA":  "VERACRUZ",
    "CUERNAVACA-IGUALA":           "MORELOS",
    "CUERNAVACA-ACAPULCO":         "GUERRERO",
    "ACAPULCO-ZIHUATANEJO":        "GUERRERO",
    "LEON-SALAMANCA":              "GUANAJUATO",
    "LEON-AGUASCALIENTES":         "JALISCO",
    "SALTILLO-MONTERREY":          "COAHUILA",
    "MONTERREY-CD VICTORIA":       "NUEVO LEON",
    "PIEDRAS NEGRAS-NUEVO LAREDO": "COAHUILA",
    "TORREON-DURANGO":             "DURANGO",
    "MAZATLAN-DURANGO":            "SINALOA",
    "MOCHIS-NAVOJOA":              "SINALOA",
    "TIJUANA-MEXICALI":            "BAJA CALIFORNIA",
    "TIJUANA-TECATE":              "BAJA CALIFORNIA",
    "LAZARO CARDENAS-URUAPAN":     "MICHOACAN",
    "PATZCUARO-URUAPAN":           "MICHOACAN",
    "CIUDAD VALLES-TAMPICO":       "SAN LUIS POTOSI",
    "CIUDAD VICTORIA-MONTERREY":   "TAMAULIPAS",
    "ARRIAGA-OCOZOCOAUTLA":        "CHIAPAS",
    "ARRIAGA-OCOZOCUAUTLA":        "CHIAPAS",
    "SALINA CRUZ-MATIAS ROMERO":   "OAXACA",
    "MITLA-TEHUANTEPEC":           "OAXACA",
    "TINAJA-ACAYUCAN":             "VERACRUZ",
    "MEX-TUXPAN":                  "VERACRUZ",
    "SAN LUIS POTOSI-QUERETARO":   "SAN LUIS POTOSI",
    "PALMILLAS-APASEO":            "QUERETARO",
    "TEPIC-PUENTE TALISMAN":       "NAYARIT",
    "APODACA-MONTERREY":           "NUEVO LEON",
    "SANTA CATALINA-NUEVA ITALIA": "MICHOACAN",
    "CUITZEO-MORELIA":             "MICHOACAN",
}


# ============================================================
# FUNCION DE NORMALIZACION
# ============================================================
def normalizar(texto):
    """Normaliza texto: mayusculas, sin acentos, sin puntuacion ruidosa."""
    if pd.isna(texto) or str(texto).strip() in ("", "-", "nan", "N/A"):
        return ""
    t = unidecode(str(texto)).upper().strip()
    t = re.sub(r"[;:'\"\[\]\(\)\{\}*#!]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ============================================================
# FUNCION PRINCIPAL: clasificar_estado
# ============================================================
def clasificar_estado(location_raw):
    """
    Dado un texto de LOCATION, devuelve un dict con:
      - estado:    nombre oficial del estado (o pais si es internacional)
      - metodo:    que catalogo lo resolvio
      - confianza: 'ALTA', 'MEDIA', 'BAJA'
    """
    texto = normalizar(location_raw)

    if not texto:
        return {"estado": "NO ESPECIFICADO", "metodo": "vacio", "confianza": "N/A"}

    # -- ETAPA 1: Internacionales (revisar ANTES que Mexico) ------
    for keyword, pais in INTERNACIONAL_KEYWORDS.items():
        kw_clean = unidecode(keyword).upper()
        if re.search(r'\b' + re.escape(kw_clean) + r'\b', texto):
            # Excepcion: si tambien menciona un estado mexicano, priorizar Mexico
            tiene_estado_mx = False
            for est_name in ESTADOS_MX:
                if est_name in texto and est_name not in ("CAMPECHE",):
                    tiene_estado_mx = True
                    break
            if not tiene_estado_mx:
                return {"estado": pais, "metodo": "internacional", "confianza": "ALTA"}

    # -- ETAPA 2: Estados explicitos en el texto ------------------
    for est_clean, est_oficial in ESTADOS_MX.items():
        if est_clean in texto:
            return {"estado": est_oficial, "metodo": "estado_explicito", "confianza": "ALTA"}

    # -- ETAPA 3: Abreviaturas ------------------------------------
    for abrev in sorted(ABREVIATURAS.keys(), key=len, reverse=True):
        abrev_clean = unidecode(abrev).upper()
        pattern = r'\b' + re.escape(abrev_clean) + r'\.?\b'
        if re.search(pattern, texto):
            return {
                "estado": ABREVIATURAS[abrev],
                "metodo": "abreviatura",
                "confianza": "ALTA"
            }

    # -- ETAPA 4: Autopistas conocidas ----------------------------
    for ruta, estado in AUTOPISTAS.items():
        ruta_clean = unidecode(ruta).upper()
        if ruta_clean in texto:
            return {"estado": estado, "metodo": "autopista", "confianza": "MEDIA"}

    # -- ETAPA 5: Ciudades/Municipios -----------------------------
    mejor_match = None
    mejor_len = 0
    for ciudad, estado in CIUDADES.items():
        ciudad_clean = unidecode(ciudad).upper()
        if ciudad_clean in texto and len(ciudad_clean) > mejor_len:
            mejor_match = (ciudad, estado)
            mejor_len = len(ciudad_clean)

    if mejor_match:
        return {
            "estado": mejor_match[1],
            "metodo": "ciudad:" + mejor_match[0],
            "confianza": "MEDIA"
        }

    # -- ETAPA 6: No identificado ---------------------------------
    return {"estado": "NO IDENTIFICADO", "metodo": "sin_match", "confianza": "N/A"}


# ============================================================
# FUNCION PARA APLICAR A UN DATAFRAME
# ============================================================
def agregar_estado(df, col_location="LOCATION"):
    """Agrega columnas ESTADO, METODO_MATCH y CONFIANZA al DataFrame."""
    resultados = df[col_location].apply(clasificar_estado)
    df["ESTADO"]        = resultados.apply(lambda r: r["estado"])
    df["METODO_MATCH"]  = resultados.apply(lambda r: r["metodo"])
    df["CONFIANZA"]     = resultados.apply(lambda r: r["confianza"])
    return df


# ============================================================
# EJEMPLO DE USO
# ============================================================
if __name__ == "__main__":

    datos_prueba = pd.DataFrame({"LOCATION": [
        "COATZACOALCOS, VERACRUZ",
        "CARR. MEX-QRO.KM 49",
        "Autopista Arriaga- Ocozocoautla KM 20+100",
        "Houston, TX, USA",
        "BALBOA PANAMA",
        "CDMX Azcapotzalco",
        "ACAPULCO, GRO.",
        "CD MADERO, TAMAULIPAS",
        "ARCO NORTE KM. 63",
        "AGUAS DEL GOLFO DE MEXICO EN LAS COORDENADAS 19 21 42.45",
        "BAHIA CONCEPCION CHILE, PUERTO DE TALCAHUANO",
        "TAD PAJARITOS",
        None,
        "-",
        "CARR. CUERNAVACA-IGUALA KM 52",
        "Cadereyta, N.L.",
        "POLOTITLAN, ESTADO DE MEXICO",
        "Algun lugar desconocido XYZ",
    ]})

    resultado = agregar_estado(datos_prueba)

    print("=" * 100)
    print("OPCION 1: CLASIFICADOR OFFLINE")
    print("=" * 100)
    for _, row in resultado.iterrows():
        loc = str(row["LOCATION"])[:50].ljust(50)
        est = row["ESTADO"].ljust(25)
        met = row["METODO_MATCH"].ljust(20)
        conf = row["CONFIANZA"]
        print("  {} -> {} [{}] ({})".format(loc, est, met, conf))

    # -- Ejemplo con archivo real --
    print()
    print("=" * 100)
    print("CARGA DE ARCHIVO REAL (si existe)")
    print("=" * 100)
    try:
        archivo = "202509_Siniestros_Marine_PROCESADO.xlsx"
        df_real = pd.read_excel(archivo)
        df_real = agregar_estado(df_real)

        print("\nTotal registros: {}".format(len(df_real)))
        print("\nDistribucion por estado:")
        print(df_real["ESTADO"].value_counts().head(20).to_string())
        print("\nDistribucion por metodo:")
        print(df_real["METODO_MATCH"].value_counts().to_string())
        print("\nNo identificados ({}):".format((df_real["ESTADO"] == "NO IDENTIFICADO").sum()))
        no_id = df_real[df_real["ESTADO"] == "NO IDENTIFICADO"]["LOCATION"].unique()
        for loc in no_id[:20]:
            print("  - {}".format(loc))
    except FileNotFoundError:
        print("  (archivo no encontrado, ejecuta con tu archivo .xlsx)")
