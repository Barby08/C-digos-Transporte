from pathlib import Path
path = Path(r'c:/Users/IKAL14/OneDrive - Kot Insurance Company AG/Códigos/Códigos Transporte/2.-Actualización Contable Marine.ipynb')
lines = path.read_text(encoding='utf-8').splitlines()
for i in range(6080, 6260):
    if i < len(lines):
        print(f'{i+1}: {lines[i]}')
