import json
from pathlib import Path

path = Path(r'c:/Users/IKAL14/OneDrive - Kot Insurance Company AG/Códigos/Códigos Transporte/2.-Actualización Contable Marine.ipynb')
nb = json.loads(path.read_text(encoding='utf-8'))
modified = False
for cell in nb['cells']:
    if cell.get('cell_type') != 'code':
        continue
    source = cell.get('source', [])
    # Find duplicate else in the key_lob matching block
    for i in range(len(source)-2):
        if source[i].strip() == "if key_lob_pago in df_export_key_lob.values:" and source[i+1].strip() == 'encontrado = True' and source[i+2].strip() == 'else:':
            # Check for duplicate else after this block
            if i+3 < len(source) and source[i+3].strip() == 'else:':
                del source[i+3]
                modified = True
                break
    cell['source'] = source
if modified:
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
    print('fixed duplicate else')
else:
    print('no duplicate else found')
