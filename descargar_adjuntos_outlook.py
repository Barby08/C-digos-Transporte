# -*- coding: utf-8 -*-
"""
Descarga automatica de adjuntos desde Outlook (escritorio).

Lee tu buzon de Outlook YA configurado en el PC (sin contrasenas ni APIs),
busca correos de remitentes especificos y guarda los adjuntos cuyo nombre
coincida con los patrones indicados.

USO:
    python descargar_adjuntos_outlook.py

Ajusta la seccion CONFIGURACION de abajo segun tus necesidades.
"""

import os
import sys
from datetime import datetime, timedelta
from fnmatch import fnmatch

import win32com.client

# Consola a prueba de caracteres unicode (evita crash con acentos/emojis)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# =========================================================================
# CONFIGURACION  <-- edita solo esta seccion
# =========================================================================

# 0) Cuenta/buzon de Outlook donde llegan los correos (nombre del almacen).
#    Los BDX llegan a esta cuenta. Debe estar agregada en el Outlook CLASICO.
CUENTA_OBJETIVO = "barbara.gomez@ikalre.ch"

# 1) Remitentes a vigilar (direcciones de correo, en minusculas).
#    Puedes poner varios. Coincide si el correo VIENE de cualquiera de estos.
#    DEJALO VACIO ( REMITENTES = [] ) para NO filtrar por remitente y bajar
#    cualquier correo cuyo adjunto coincida con los patrones (mas seguro si
#    no estas 100% segura de quien los envia).
REMITENTES = [
    # "miguel.a.villagran@ikalre.ch",
    # "miguel.a.villagran@koticag.ch",
]

# 2) Patrones de nombre de adjunto a descargar (estilo comodin, sin importar
#    mayus/minus). Ejemplos:
#       "*.xlsx"          -> cualquier Excel
#       "Base_*.xlsx"     -> Excel que empiece con "Base_"
#       "*Transporte*"    -> cualquier archivo que contenga "Transporte"
PATRONES_ADJUNTO = [
    "BDX PEMEX NCGL-070-1000773 -*.xlsx",
    "BDX PEMEX NCGL-070-1002258 REAS*.xlsx",
    "BDX PEMEX NCGL-070-1000773 -*.xls",
    "BDX PEMEX NCGL-070-1002258 REAS*.xls",    
    "Bordereaux_Inbursa_Casco_Pandi_*.xlsx",
    "Bordereaux_Inbursa_Casco_Pandi_*.xls",
    "Bordereaux_Inbursa_Casco_Pandi_Transporte_09-11_*.xlsx",
    "Bordereaux_Inbursa_Casco_Pandi_Transporte_09-11_*.xls",
    "Bordereaux_Inbursa_Casco_Pandi_Transporte_11-13_*.xlsx",
    "Bordereaux_Inbursa_Casco_Pandi_Transporte_11-13_*.xls",
    "Bordereaux_Inbursa_Casco_Pandi_Transportes_13-15_*.xlsx",
    "Bordereaux_Inbursa_Casco_Pandi_Transportes_13-15_*.xls",
    "Bordereaux_Mapfre_Casco_Pandi_Transportes_21-23_*.xlsx",
    "Bordereaux_Mapfre_Casco_Pandi_Transportes_21-23_*.xls",
    "Bordereaux_Seguros Atlas E01-2-60-3_*.xlsx",
    "Bordereaux_Seguros Atlas E01-2-60-3_*.xls",
    "Bordereaux_Seguros Atlas E01-2-60-10_*.xlsx",    
    "Bordereaux_Seguros Atlas E01-2-60-10_*.xls",
    "Bordereaux_Inbursa_Aguas Profundas_12-14_*.xlsx",
    "Bordereaux_Inbursa_Aguas Profundas_12-14_*.xls"
]

# 3) Carpeta donde se guardaran los adjuntos (se crea si no existe).
#Detectar el añomes a trabajar, mes actual -1
mesactual=datetime.now().month
mes=mesactual-1 
if mes==0:
    mes=12
    anio=datetime.now().year-1
else:
    anio=datetime.now().year    
añomes=str(anio)+str(mes).zfill(2)
print("AñoMes a trabajar: ",añomes)

#Crear carpeta del añomes si no existe
CARPETA_DESTINO = os.path.join(r"C:\Users\IKAL14\Documents\Integral\Marine\Insumos",añomes)
if not os.path.exists(CARPETA_DESTINO):
    os.makedirs(CARPETA_DESTINO)    



# 4) Cuantos dias hacia atras revisar (para no recorrer todo el buzon).
DIAS_ATRAS = 15

# 5) Solo procesar correos NO leidos? (True = solo no leidos)
SOLO_NO_LEIDOS = False

# 6) Marcar el correo como leido despues de descargar sus adjuntos?
MARCAR_COMO_LEIDO = False

# 7) Si el archivo ya existe en destino: "omitir" o "renombrar".
SI_YA_EXISTE = "renombrar"

# 8) Carpeta de Outlook a revisar. 6 = Bandeja de entrada (Inbox).
#    Deja 6 para la bandeja principal. (Para subcarpetas ver nota al final.)
CARPETA_OUTLOOK = 6

# =========================================================================
# FIN DE LA CONFIGURACION
# =========================================================================


def obtener_smtp(mensaje):
    """Devuelve la direccion SMTP real del remitente.

    Para correos internos (Exchange) SenderEmailAddress puede devolver una
    cadena X.500 rara; en ese caso se intenta resolver a SMTP.
    """
    try:
        tipo = mensaje.SenderEmailType
    except Exception:
        tipo = ""

    if tipo == "EX":
        # Correo interno Exchange: resolver via el objeto ExchangeUser
        try:
            remitente = mensaje.Sender
            usuario_ex = remitente.GetExchangeUser()
            if usuario_ex is not None and usuario_ex.PrimarySmtpAddress:
                return usuario_ex.PrimarySmtpAddress.lower()
        except Exception:
            pass
        # Alternativa: propiedad PR_SMTP_ADDRESS
        try:
            PR_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
            smtp = mensaje.Sender.PropertyAccessor.GetProperty(PR_SMTP)
            if smtp:
                return smtp.lower()
        except Exception:
            pass

    try:
        return (mensaje.SenderEmailAddress or "").lower()
    except Exception:
        return ""


def obtener_bandeja(namespace):
    """Devuelve la Bandeja de entrada de la cuenta CUENTA_OBJETIVO.

    Si CUENTA_OBJETIVO esta vacio, usa la cuenta por defecto.
    Si no se encuentra la cuenta, muestra las disponibles y termina.
    """
    objetivo = (CUENTA_OBJETIVO or "").lower().strip()

    if not objetivo:
        return namespace.GetDefaultFolder(CARPETA_OUTLOOK)

    # Buscar el almacen (store) cuyo nombre coincida con la cuenta objetivo
    disponibles = []
    for store in namespace.Stores:
        try:
            nombre = (store.DisplayName or "").lower()
        except Exception:
            nombre = ""
        disponibles.append(nombre)
        if objetivo in nombre:
            try:
                # Bandeja de entrada de ESE almacen
                return store.GetDefaultFolder(CARPETA_OUTLOOK)
            except Exception:
                # Alternativa: buscar carpeta "Inbox"/"Bandeja de entrada"
                raiz = store.GetRootFolder()
                for f in raiz.Folders:
                    if f.Name.lower() in ("inbox", "bandeja de entrada"):
                        return f

    print(f"[ERROR] No encontre la cuenta '{CUENTA_OBJETIVO}' en Outlook.")
    print("Cuentas/almacenes disponibles ahora mismo:")
    for d in disponibles:
        print(f"   - {d}")
    print("\n-> Asegurate de estar en el Outlook CLASICO con esa cuenta agregada.")
    sys.exit(1)


def adjunto_coincide(nombre_archivo):
    """True si el nombre del adjunto coincide con algun patron configurado."""
    nombre = nombre_archivo.lower()
    return any(fnmatch(nombre, patron.lower()) for patron in PATRONES_ADJUNTO)


def ruta_destino(nombre_archivo):
    """Calcula la ruta final aplicando la politica SI_YA_EXISTE."""
    destino = os.path.join(CARPETA_DESTINO, nombre_archivo)
    if not os.path.exists(destino):
        return destino

    if SI_YA_EXISTE == "omitir":
        return None

    # renombrar: agrega sufijo numerico
    base, ext = os.path.splitext(nombre_archivo)
    i = 1
    while True:
        candidato = os.path.join(CARPETA_DESTINO, f"{base}_{i}{ext}")
        if not os.path.exists(candidato):
            return candidato
        i += 1


def main():
    remitentes = [r.lower().strip() for r in REMITENTES if r.strip()]

    os.makedirs(CARPETA_DESTINO, exist_ok=True)

    print("Conectando con Outlook...")
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    carpeta = obtener_bandeja(namespace)

    items = carpeta.Items
    try:
        items.Sort("[ReceivedTime]", True)  # mas recientes primero
    except Exception:
        pass

    # Filtro por fecha en Python (robusto ante configuracion regional).
    # NOTA: NO usamos Items.Restrict porque exige el formato de fecha regional
    # de Windows y en es-ES/es-MX devuelve una lista vacia sin avisar.
    desde = datetime.now() - timedelta(days=DIAS_ATRAS)

    print(f"Cuenta:     {CUENTA_OBJETIVO or '(por defecto)'}")
    print(f"Revisando correos de los ultimos {DIAS_ATRAS} dias...")
    print(f"Remitentes: {', '.join(remitentes) if remitentes else '(cualquiera)'}")
    print(f"Patrones:   {len(PATRONES_ADJUNTO)} configurados")
    print(f"Destino:    {CARPETA_DESTINO}\n")

    correos_procesados = 0
    archivos_guardados = 0

    for mensaje in items:
        # Solo correos normales
        try:
            if mensaje.Class != 43:  # 43 = MailItem
                continue
        except Exception:
            continue

        # Filtro por fecha (en Python)
        try:
            if mensaje.ReceivedTime.replace(tzinfo=None) < desde:
                continue
        except Exception:
            pass

        if SOLO_NO_LEIDOS:
            try:
                if not mensaje.UnRead:
                    continue
            except Exception:
                pass

        smtp = obtener_smtp(mensaje)
        # Si hay lista de remitentes, filtrar; si esta vacia, aceptar cualquiera
        if remitentes and smtp not in remitentes:
            continue

        # Este correo es de un remitente vigilado
        try:
            asunto = mensaje.Subject
            recibido = mensaje.ReceivedTime
        except Exception:
            asunto, recibido = "(sin asunto)", ""

        adjuntos = mensaje.Attachments
        guardados_este_correo = 0

        for i in range(1, adjuntos.Count + 1):
            adj = adjuntos.Item(i)
            nombre = adj.FileName
            if not adjunto_coincide(nombre):
                continue

            destino = ruta_destino(nombre)
            if destino is None:
                print(f"   - OMITIDO (ya existe): {nombre}")
                continue

            try:
                adj.SaveAsFile(destino)
                print(f"   + Guardado: {os.path.basename(destino)}")
                guardados_este_correo += 1
                archivos_guardados += 1
            except Exception as e:
                print(f"   ! Error guardando {nombre}: {e}")

        if guardados_este_correo > 0:
            correos_procesados += 1
            print(f"  Correo: '{asunto}'  ({recibido})  de {smtp}\n")
            if MARCAR_COMO_LEIDO:
                try:
                    mensaje.UnRead = False
                    mensaje.Save()
                except Exception:
                    pass

    print("-" * 60)
    print(f"Listo. Correos con adjuntos descargados: {correos_procesados}")
    print(f"Archivos guardados: {archivos_guardados}")
    if archivos_guardados == 0:
        print("(No se encontraron adjuntos que coincidan con los criterios.)")


if __name__ == "__main__":
    main()
