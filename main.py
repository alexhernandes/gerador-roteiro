"""
Gerador de Roteiro

Uso: python main.py
"""

from gerar_roteiro import gerar_roteiro

if __name__ == "__main__":
    try:
        gerar_roteiro()
    except KeyboardInterrupt:
        print("\nTchau!")
    except Exception as e:
        print(f"\nErro: {e}\n")
        input("Aperte ENTER para sair...")