"""
Gerador de Roteiro

Uso: python main.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from gerar_roteiro import gerar_roteiro

if __name__ == "__main__":
    try:
        gerar_roteiro()
    except KeyboardInterrupt:
        print("\nTchau!")
    except Exception as e:
        print(f"\nErro: {e}\n")
        input("Aperte ENTER para sair.")