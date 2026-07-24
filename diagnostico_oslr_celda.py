# =============================================================================
# DIAGNÓSTICO OSLR — Trazabilidad paso a paso para un siniestro específico
# Pegar como celda nueva JUSTO DESPUÉS del bloque "OSLR Calculation" de la
# Sección 6 (después de que existan: oslr_col, df_log_zereo_oslr,
# df_ajustes_net_reserve, LEGACY) y ANTES de la Sección 7.
# =============================================================================

def diagnosticar_oslr(claim_number, df_update_db, oslr_col, AñoMes,
                       df_log_zereo_oslr=None, df_ajustes_net_reserve=None):
    """
    Reconstruye y muestra en consola el paso a paso del cálculo de OSLR
    para un CLAIM NUMBER específico, replicando la lógica de la Sección 6:
    (1) fórmula base max(max(GR-DED,0)-Cumulative CLAIMS PAID,0),
    (2) validación contra Net Reserve (USD) del BDX,
    (3) reglas de zereo que lo hayan afectado (vía df_log_zereo_oslr).

    Parámetros
    ----------
    claim_number : str
        Número de siniestro a diagnosticar, ej. '108265/2018'.
    df_update_db : pd.DataFrame
        Base principal del notebook, ya con 'GROSS RESERVE {AñoMes}',
        'DEDUCTIBLE {AñoMes}', 'Cumulative CLAIMS PAID', 'Net Reserve (USD)'
        y la columna oslr_col calculados (Sección 6).
    oslr_col : str
        Nombre de la columna de OSLR del mes en curso, ej. 'OSLR Inward 202509'.
    AñoMes : int
        Periodo en formato AAAAMM, usado para armar nombres de columna.
    df_log_zereo_oslr : pd.DataFrame, opcional
        Log de reglas de zereo (generado en la Sección 6). Si no se pasa,
        se omite el paso 3.
    df_ajustes_net_reserve : pd.DataFrame, opcional
        Log de ajustes contra Net Reserve (USD). Si no se pasa, se omite
        la nota de ese ajuste.

    Retorna
    -------
    pd.DataFrame
        Subconjunto de df_update_db con las filas del siniestro (una fila
        por KEY LOB si hay multi-deducible). None si no se encontró el
        siniestro o si faltan columnas obligatorias.

    Excepciones manejadas
    ---------------------
    - KeyError: columna obligatoria ausente en df_update_db -> se informa
      cuál falta y se detiene el diagnóstico sin lanzar el error hacia arriba.
    - Exception genérica: se captura, se informa el mensaje y se retorna None,
      para no interrumpir la ejecución del resto del notebook.
    """
    claim_number = str(claim_number).strip()
    cols_obligatorias = [
        'CLAIM NUMBER', 'KEY LOB', 'INWARD POLICY N°', 'STATUS',
        f'GROSS RESERVE {AñoMes}', f'DEDUCTIBLE {AñoMes}',
        'Cumulative CLAIMS PAID', 'Net Reserve (USD)', oslr_col,
    ]

    try:
        faltantes = [c for c in cols_obligatorias if c not in df_update_db.columns]
        if faltantes:
            raise KeyError(faltantes)

        df_claim = df_update_db[
            df_update_db['CLAIM NUMBER'].astype(str).str.strip() == claim_number
        ].copy()

        print('\n' + '=' * 95)
        print(f'DIAGNÓSTICO OSLR — CLAIM NUMBER: {claim_number}')
        print('=' * 95)

        if df_claim.empty:
            print(f"⚠️  No se encontró el CLAIM NUMBER '{claim_number}' en df_update_db.")
            print("    Revisa formato (espacios, '/', año) o si el siniestro es nuevo/legacy.")
            return None

        for _, row in df_claim.iterrows():
            key_lob = row['KEY LOB']
            policy = row['INWARD POLICY N°']
            status = row['STATUS']
            es_legacy = str(policy).strip() in LEGACY

            print('\n' + '-' * 95)
            print(f"KEY LOB: {key_lob}  |  Póliza: {policy}  |  STATUS: {status}"
                  f"{'  |  ⚠️ LEGACY (OSLR congelado en 0)' if es_legacy else ''}")
            print('-' * 95)

            gr = row[f'GROSS RESERVE {AñoMes}']
            ded = row[f'DEDUCTIBLE {AñoMes}']
            cum_paid = row['Cumulative CLAIMS PAID']
            net_reserve = row['Net Reserve (USD)']
            oslr_final = row[oslr_col]

            paso1 = max((gr or 0) - (ded or 0), 0)
            paso2 = max(paso1 - (cum_paid or 0), 0)

            print(f"  Paso 1 — Fórmula base:")
            print(f"    GROSS RESERVE {AñoMes}        : {gr:,.2f}")
            print(f"    DEDUCTIBLE {AñoMes}           : {ded:,.2f}")
            print(f"    max(GR - DED, 0)              = {paso1:,.2f}")
            print(f"    Cumulative CLAIMS PAID        : {cum_paid:,.2f}")
            print(f"    max(paso1 - Cum.Claims, 0)    = {paso2:,.2f}   <- OSLR calculado (antes de ajustes)")

            print(f"\n  Paso 2 — Validación contra Net Reserve (USD):")
            print(f"    Net Reserve (USD) del BDX     : {net_reserve:,.2f}")
            if df_ajustes_net_reserve is not None and not df_ajustes_net_reserve.empty:
                ajuste = df_ajustes_net_reserve[
                    df_ajustes_net_reserve['CLAIM NUMBER'].astype(str).str.strip() == claim_number
                ]
                if not ajuste.empty:
                    print(f"    -> Se forzó el OSLR a Net Reserve (USD) por STATUS='P' y Net Reserve≈0.")
                else:
                    print(f"    -> Sin ajuste (no aplica: STATUS≠'P', Net Reserve≠0, o ya coincidía).")

            print(f"\n  Paso 3 — Reglas de zereo aplicadas:")
            if df_log_zereo_oslr is not None and not df_log_zereo_oslr.empty:
                df_log_claim = df_log_zereo_oslr[
                    df_log_zereo_oslr['CLAIM NUMBER'].astype(str).str.strip() == claim_number
                ]
                if not df_log_claim.empty:
                    for _, r in df_log_claim.iterrows():
                        print(f"    - [{r['REGLA']}] {r['DETALLE']}  |  "
                              f"OSLR ANTES={r['OSLR ANTES']:,.2f} -> DESPUÉS={r['OSLR DESPUES']:,.2f}")
                else:
                    print("    Ninguna regla de zereo modificó este siniestro.")
            else:
                print("    (df_log_zereo_oslr no disponible — corre la celda de OSLR primero)")

            print(f"\n  ✅ OSLR FINAL ({oslr_col}): {oslr_final:,.2f}")

        return df_claim

    except KeyError as e:
        print(f"❌ Faltan columnas obligatorias en df_update_db para diagnosticar: {e}. "
              f"Corre primero la celda de cálculo de OSLR (Sección 6).")
        return None
    except Exception as e:
        print(f"❌ Error inesperado al diagnosticar el siniestro {claim_number}: {e}")
        return None


# ------------------- Ejecución para el siniestro solicitado -------------------
_ = diagnosticar_oslr(
    claim_number='108265/2018',
    df_update_db=df_update_db,
    oslr_col=oslr_col,
    AñoMes=AñoMes,
    df_log_zereo_oslr=df_log_zereo_oslr if 'df_log_zereo_oslr' in globals() else None,
    df_ajustes_net_reserve=df_ajustes_net_reserve if 'df_ajustes_net_reserve' in globals() else None,
)
