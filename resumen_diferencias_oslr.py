# =============================================================================
# RESUMEN DE DIFERENCIAS OSLR vs BASE MANUAL — masivo, con causa por siniestro
# Pegar como celda nueva justo DESPUÉS de la Sección 10 (Validación OSLR vs BDX)
# de "2.-Actualizacion Contable Marine.ipynb". En ese punto ya están en memoria:
# df_update_db (con 'OSLR Inward' ya renombrado, Sección 8), LEGACY (Sección 6),
# df_log_zereo_oslr y df_ajustes_net_reserve (Sección 6), ruta_incidencias y
# AñoMes (Sección 2), y _limpiar_llave (Sección 10).
#
# Generaliza diagnostico_oslr_celda.py (que audita UN siniestro a la vez) a
# TODOS los siniestros con diferencia contra una base manual (un Excel que se
# mantiene a mano, ej. "{AñoMes}_Siniestros_Marine_MANUAL.xlsx"), clasificando
# automáticamente la causa más probable de cada diferencia:
#   - Sin match en una de las dos bases (siniestro nuevo, no cargado, o
#     Claim Number con formato distinto entre fuentes).
#   - LEGACY (el notebook congela el OSLR en 0/mes anterior para estas pólizas
#     por diseño, aunque la base manual traiga otro valor).
#   - Zereado por alguna de las reglas de auditoría de la Sección 6 (se toma
#     la(s) regla(s) real(es) de df_log_zereo_oslr, no una lista fija, para
#     no desactualizarse si cambian las reglas).
#   - Ajustado a Net Reserve (USD) del BDX (paso 2 de la lógica de OSLR).
#   - Ninguna de las anteriores -> diferencia sin explicar por las reglas
#     conocidas: candidato real a error de cálculo o de dato de origen.
# =============================================================================

import shutil
import tempfile
import time


def resumen_diferencias_oslr_vs_manual(
    path_manual_excel, df_update_db, LEGACY, df_log_zereo_oslr, df_ajustes_net_reserve,
    ruta_incidencias, AñoMes, sheet_name=0, tolerancia=1.0,
):
    """
    Compara el OSLR final calculado por el notebook (df_update_db['OSLR Inward'],
    agregado por CLAIM NUMBER) contra una base manual (Excel externo, agregado
    igual por CLAIM NUMBER), y para cada siniestro cuya diferencia supera la
    tolerancia, clasifica la causa más probable reutilizando lo que ya calculó
    la Sección 6: reglas de zereo (df_log_zereo_oslr), ajuste contra Net Reserve
    (df_ajustes_net_reserve) y pólizas LEGACY.

    La comparación se hace a nivel CLAIM NUMBER (no KEY LOB) porque la base
    manual no trae una columna equivalente a KEY LOB para cruzar de forma
    confiable multi-deducible; sumar por CLAIM NUMBER es el mismo criterio que
    ya usa la hoja "Siniestro" de la Sección 10.

    Parámetros
    ----------
    path_manual_excel : str
        Ruta al Excel de la base manual (ej. "..._Siniestros_Marine_MANUAL.xlsx").
        Debe traer, al menos, 'CLAIM NUMBER' y 'OSLR Inward'.
    df_update_db : pd.DataFrame
        Base principal del notebook, YA con la columna 'OSLR Inward' renombrada
        (después de la Sección 8) y 'INWARD POLICY N°', 'STATUS', 'KEY LOB'.
    LEGACY : list[str]
        Lista de INWARD POLICY N° legacy (variable ya armada en la Sección 6).
    df_log_zereo_oslr : pd.DataFrame
        Log de reglas de zereo de la Sección 6 (columnas CLAIM NUMBER, REGLA, ...).
    df_ajustes_net_reserve : pd.DataFrame
        Log de ajustes contra Net Reserve (USD) de la Sección 6.
    ruta_incidencias : str
        Carpeta de Incidencias del período (Sección 2), donde se exporta el
        resumen en Excel.
    AñoMes : int
        Periodo en formato AAAAMM, usado solo para el nombre del archivo exportado.
    sheet_name : str o int, default 0
        Hoja del Excel manual a leer, si no es la primera.
    tolerancia : float, default 1.0
        Diferencia mínima (USD, valor absoluto) para que un siniestro entre al
        resumen. Diferencias menores se consideran redondeo y se descartan.

    Retorna
    -------
    pd.DataFrame
        Columnas: CLAIM NUMBER, INWARD POLICY N°, STATUS, Filas KEY LOB,
        OSLR Manual, OSLR Calculado, Diferencia, Causa, Detalle. Ordenado por
        |Diferencia| descendente. Vacío (mismas columnas) si ningún siniestro
        supera la tolerancia. None si falta el archivo o columnas obligatorias.

    Excepciones manejadas
    ---------------------
    - FileNotFoundError: no existe path_manual_excel -> se informa y se detiene
      sin lanzar el error hacia arriba.
    - PermissionError: el archivo está bloqueado (típico en archivos de OneDrive/
      SharePoint recién guardados, mientras el motor de sincronización todavía
      está subiendo el cambio) -> se reintenta unas veces con espera antes de
      rendirse, copiando siempre a un temporal para no depender del lock directo.
    - KeyError: falta 'CLAIM NUMBER' u 'OSLR Inward' en la base manual, o falta
      'OSLR Inward' en df_update_db (corre esta celda DESPUÉS de la Sección 8) ->
      se informa cuál falta y se detiene.
    - Exception genérica: se captura, se informa el mensaje y se retorna None,
      para no interrumpir el resto del notebook.
    """
    try:
        if not os.path.exists(path_manual_excel):
            raise FileNotFoundError(f"No se encontró la base manual en: {path_manual_excel}")

        # OneDrive/SharePoint suele dejar el archivo brevemente bloqueado mientras
        # sincroniza un guardado reciente, aunque ya esté cerrado en Excel. Copiarlo
        # a un temporal evita ese PermissionError transitorio; se reintenta un par
        # de veces con espera corta antes de rendirse.
        tmp_dir = tempfile.mkdtemp(prefix='oslr_manual_')
        path_tmp = os.path.join(tmp_dir, os.path.basename(path_manual_excel))
        ultimo_error = None
        for intento in range(5):
            try:
                shutil.copy2(path_manual_excel, path_tmp)
                ultimo_error = None
                break
            except PermissionError as e:
                ultimo_error = e
                print(f"  ⏳ Archivo bloqueado (probablemente sincronizando en OneDrive), reintento {intento + 1}/5...")
                time.sleep(3)
        if ultimo_error is not None:
            raise PermissionError(
                f"No se pudo leer '{path_manual_excel}' tras varios intentos: {ultimo_error}. "
                "Verifica en el icono de OneDrive que el archivo terminó de sincronizar (nube/check verde) e intenta de nuevo."
            )

        df_manual_raw = pd.read_excel(path_tmp, sheet_name=sheet_name)
        faltantes_manual = {'CLAIM NUMBER', 'OSLR Inward'} - set(df_manual_raw.columns)
        if faltantes_manual:
            raise KeyError(f"La base manual no trae las columnas esperadas: {faltantes_manual}")

        faltantes_calc = {'CLAIM NUMBER', 'INWARD POLICY N°', 'STATUS', 'OSLR Inward'} - set(df_update_db.columns)
        if faltantes_calc:
            raise KeyError(
                f"df_update_db no trae las columnas esperadas: {faltantes_calc}. "
                "Corre esta celda DESPUÉS de la Sección 8 (rename de OSLR Inward)."
            )

        print('\n' + '=' * 95)
        print(f'RESUMEN DE DIFERENCIAS OSLR vs BASE MANUAL — {AñoMes}')
        print('=' * 95)

        # --- Normalización de llave (misma lógica que _limpiar_llave de la Sección 10) ---
        limpiar = _limpiar_llave if '_limpiar_llave' in globals() else (lambda s: s.astype(str).str.strip())

        df_manual = df_manual_raw.copy()
        df_manual['CLAIM NUMBER'] = limpiar(df_manual['CLAIM NUMBER'])
        df_manual['OSLR Inward'] = pd.to_numeric(df_manual['OSLR Inward'], errors='coerce').fillna(0)
        manual_por_claim = (
            df_manual.groupby('CLAIM NUMBER', as_index=False)['OSLR Inward']
            .sum()
            .rename(columns={'OSLR Inward': 'OSLR Manual'})
        )

        df_calc = df_update_db.copy()
        df_calc['CLAIM NUMBER'] = limpiar(df_calc['CLAIM NUMBER'])
        df_calc['INWARD POLICY N°'] = df_calc['INWARD POLICY N°'].astype(str).str.strip()
        calc_por_claim = df_calc.groupby('CLAIM NUMBER', as_index=False).agg(**{
            'OSLR Calculado': ('OSLR Inward', 'sum'),
            'INWARD POLICY N°': ('INWARD POLICY N°', 'first'),
            'STATUS': ('STATUS', lambda s: ', '.join(sorted(set(s.astype(str).str.strip())))),
            'Filas KEY LOB': ('CLAIM NUMBER', 'count'),
        })

        resumen = manual_por_claim.merge(calc_por_claim, on='CLAIM NUMBER', how='outer')
        resumen['OSLR Manual'] = resumen['OSLR Manual'].fillna(0)
        resumen['OSLR Calculado'] = resumen['OSLR Calculado'].fillna(0)
        resumen['Diferencia'] = resumen['OSLR Manual'] - resumen['OSLR Calculado']

        resumen = resumen[resumen['Diferencia'].abs() > tolerancia].copy()
        if resumen.empty:
            print(f'✅ Ningún siniestro supera la tolerancia (${tolerancia:,.2f}). Bases conciliadas.')
            return resumen

        # --- Contexto ya calculado en la Sección 6, para clasificar la causa ---
        reglas_por_claim = {}
        if df_log_zereo_oslr is not None and not df_log_zereo_oslr.empty:
            reglas_por_claim = (
                df_log_zereo_oslr.assign(**{'CLAIM NUMBER': limpiar(df_log_zereo_oslr['CLAIM NUMBER'])})
                .groupby('CLAIM NUMBER')['REGLA']
                .apply(lambda s: ', '.join(sorted(s.dropna().astype(str).unique())))
                .to_dict()
            )
        claims_ajuste_net_reserve = set()
        if df_ajustes_net_reserve is not None and not df_ajustes_net_reserve.empty:
            claims_ajuste_net_reserve = set(limpiar(df_ajustes_net_reserve['CLAIM NUMBER']))
        claims_en_manual = set(manual_por_claim['CLAIM NUMBER'])
        claims_en_calc = set(calc_por_claim['CLAIM NUMBER'])

        def _clasificar(row):
            claim = row['CLAIM NUMBER']
            if claim not in claims_en_calc:
                return 'Sin match en base calculada', 'El Claim Number no está en df_update_db (¿nuevo, no cargado, o formato distinto en la base manual?).'
            if claim not in claims_en_manual:
                return 'Sin match en base manual', 'El Claim Number no está en la base manual (¿pendiente de captura, o formato distinto?).'
            if str(row['INWARD POLICY N°']).strip() in LEGACY:
                return 'Legacy', 'Póliza LEGACY: el notebook congela el OSLR (0 / valor del mes anterior) por diseño; la base manual puede traer otro valor si no se actualizó con el mismo criterio.'
            if claim in reglas_por_claim:
                regla = reglas_por_claim[claim]
                nota_base_anterior = ' (usa OSLR/variables del mes anterior)' if re.search(r'anterior|previo|cambios en el mes', regla, re.IGNORECASE) else ''
                return f'Zereado por regla: {regla}', f'Ver Log_Zereo_OSLR.xlsx para el detalle{nota_base_anterior}.'
            if claim in claims_ajuste_net_reserve:
                return 'Ajuste vs Net Reserve BDX', 'El OSLR se forzó a Net Reserve (USD) del BDX (paso 2 de la lógica de OSLR, STATUS=P y Net Reserve≈0).'
            return 'Sin explicar', 'Ninguna regla conocida movió este siniestro: revisar cálculo (GROSS RESERVE/DEDUCTIBLE/Cumulative CLAIMS PAID) o el dato de origen en ambas bases.'

        resumen[['Causa', 'Detalle']] = resumen.apply(lambda r: pd.Series(_clasificar(r)), axis=1)
        resumen = resumen.sort_values(by='Diferencia', key=lambda s: s.abs(), ascending=False).reset_index(drop=True)

        resumen = resumen[[
            'CLAIM NUMBER', 'INWARD POLICY N°', 'STATUS', 'Filas KEY LOB',
            'OSLR Manual', 'OSLR Calculado', 'Diferencia', 'Causa', 'Detalle',
        ]]

        print(f"\nSiniestros con diferencia > ${tolerancia:,.2f}: {len(resumen)}")
        print(f"Diferencia neta (Manual - Calculado): ${resumen['Diferencia'].sum():,.2f}")
        print('\nResumen por causa (cantidad de siniestros y $ absoluto):')
        resumen_causa = resumen.groupby('Causa').agg(
            **{'N Siniestros': ('CLAIM NUMBER', 'count'), '$ Diferencia (abs)': ('Diferencia', lambda s: s.abs().sum())}
        ).sort_values('$ Diferencia (abs)', ascending=False)
        print(resumen_causa.to_string())

        path_out = f'{ruta_incidencias}/Resumen_Diferencias_OSLR_vs_Manual_{AñoMes}.xlsx'
        resumen.to_excel(path_out, index=False)
        print(f"\n📄 Exportado: {path_out}")

        return resumen

    except FileNotFoundError as e:
        print(f"❌ {e}")
        return None
    except PermissionError as e:
        print(f"❌ {e}")
        return None
    except KeyError as e:
        print(f"❌ {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado al armar el resumen de diferencias: {e}")
        return None
    finally:
        if 'tmp_dir' in locals():
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ------------------------- Ejecución -------------------------
# Ajusta la ruta de la base manual a la del período que estés validando.
PATH_MANUAL_OSLR = rf"C:\Users\IKAL14\OneDrive - Kot Insurance Company AG\Transporte, Carga y Embarcaciones\{AñoMes}_Siniestros_Marine_MANUAL.xlsx"

df_resumen_diferencias_manual = resumen_diferencias_oslr_vs_manual(
    path_manual_excel=PATH_MANUAL_OSLR,
    df_update_db=df_update_db,
    LEGACY=LEGACY,
    df_log_zereo_oslr=df_log_zereo_oslr if 'df_log_zereo_oslr' in globals() else None,
    df_ajustes_net_reserve=df_ajustes_net_reserve if 'df_ajustes_net_reserve' in globals() else None,
    ruta_incidencias=ruta_incidencias,
    AñoMes=AñoMes,
)
