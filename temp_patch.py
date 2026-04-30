import json
from pathlib import Path

path = Path(r'c:/Users/IKAL14/OneDrive - Kot Insurance Company AG/Códigos/Códigos Transporte/2.-Actualización Contable Marine.ipynb')
nb = json.loads(path.read_text(encoding='utf-8'))
modified = False
old_block = ("                if 'KEY LOB VALIDACION' in pago.index and df_export_key_lob is not None:\n"
             "                    key_lob_pago = str(pago['KEY LOB VALIDACION']).strip().upper()\n"
             "                # El procesamiento crea KEY LOB y hace merge, así que verificamos si ese KEY LOB existe en la base final\n"
             "\n"
             "                    if key_lob_pago in df_export_key_lob.values:\n"
             "                    key_lob_pago = str(pago['KEY LOB VALIDACION']).strip()\n"
             "\n"
             "                    # Verificar si este KEY LOB existe en la base final (df_export)\n"
             "                    if key_lob_pago in df_export['KEY LOB'].astype(str).values:\n"
             "                        encontrado = True\n")

new_block = ("                if 'KEY LOB VALIDACION' in pago.index and df_export_key_lob is not None:\n"
             "                    key_lob_pago = str(pago['KEY LOB VALIDACION']).strip().upper()\n"
             "\n"
             "                    # Verificar si este KEY LOB existe en la base final (df_export)\n"
             "                    if key_lob_pago in df_export_key_lob.values:\n"
             "                        encontrado = True\n"
             "                    else:\n"
             "                        # Verificar si hay algún registro con Claims Reference que coincida parcialmente\n")

for cell in nb['cells']:
    if cell.get('cell_type') == 'code':
        src = ''.join(cell.get('source', []))
        if old_block in src:
            cell['source'] = [src.replace(old_block, new_block)]
            modified = True

if modified:
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
    print('patched')
else:
    print('no match found')
