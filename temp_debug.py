from pathlib import Path
import json
path = Path(r'c:/Users/IKAL14/OneDrive - Kot Insurance Company AG/Códigos/Códigos Transporte/2.-Actualización Contable Marine.ipynb')
nb = json.loads(path.read_text(encoding='utf-8'))
output=[]
for cell_index, cell in enumerate(nb['cells']):
    if cell.get('cell_type') != 'code':
        continue
    source = cell.get('source', [])
    joined = ''.join(source)
    if 'if key_lob_pago in df_export_key_lob.values' in joined:
        output.append(f'cell_index={cell_index}')
        for i, line in enumerate(source):
            if 'if key_lob_pago in df_export_key_lob.values' in line or 'else:' in line or 'claims_ref' in line or 'key_lob_pago' in line:
                output.append(f'{i}: {repr(line)}')
Path('debug_output2.txt').write_text('\n'.join(output), encoding='utf-8')
