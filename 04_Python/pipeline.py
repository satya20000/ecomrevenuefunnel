from pathlib import Path
import argparse
from olist import funnel
if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Olist B2B Revenue Funnel')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    c=funnel(args.root)
    print('\n'.join(c.findings))
