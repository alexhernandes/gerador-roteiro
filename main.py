"""
Gerador de Roteiro

Uso: python main.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
MODULO = SRC / "gerar_roteiro.py"

if not MODULO.is_file():
    print(f"\nErro: módulo não encontrado em:\n  {MODULO}\n")
    print("Certifique-se de executar main.py na pasta raiz do projeto.")
    print("A pasta src/ deve conter gerar_roteiro.py e os demais módulos.\n")
    input("Aperte ENTER para sair...")
    sys.exit(1)

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gerar_roteiro import gerar_roteiro

if __name__ == "__main__":
    try:
        gerar_roteiro()
    except KeyboardInterrupt:
        print("\nTchau!")
    except Exception as e:
        print(f"\nErro: {e}\n")
        input("Aperte ENTER para sair...")