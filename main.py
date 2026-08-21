import json
import sys

from pathlib import Path


def spectral_radius(matrix):
    try:
        import numpy as np
        values = np.linalg.eigvals(np.array(matrix, dtype=float))
        return float(max(abs(values)))
    except Exception:
        return None


def main():
    if len(sys.argv) < 2:
        print('Usage: python main.py examples/himeko_nova_cycle_demo.json')
        return

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding='utf-8'))

    print('=' * 40)
    print('HSR Infinite Cycle Analyzer')
    print('=' * 40)
    print('Example:', data.get('name'))

    rho = spectral_radius(data.get('matrix', []))
    print('Spectral Radius:', rho)

    if rho is not None:
        if rho > 1:
            print('Linear Model: Possible growth direction')
        elif rho == 1:
            print('Linear Model: Critical cycle')
        else:
            print('Linear Model: Resource decay')

    print('Note: Linear result requires battle simulation verification.')


if __name__ == '__main__':
    main()
