import argparse
from pathlib import Path

from metaspace import SMInstance

from util import download_dataset, download_file, get_dataset_ids_from_csv_file, envs


def main():
    help_msg = 'Download datasets files and metadata.'
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument(
        '--datasets_file',
        type=str,
        required=True,
        help='Path to file that contains dataset_ids in CSV format',
    )
    parser.add_argument(
        '--env',
        type=str,
        choices=envs.keys(),
        required=True,
        help='Name of environment: beta, staging, prod',
    )
    parser.add_argument('--api_key', type=str, required=True, help='API KEY')
    args = parser.parse_args()

    dataset_ids = get_dataset_ids_from_csv_file(args.datasets_file)

    p = Path('.')
    sm = SMInstance(host=envs[args.env], api_key=args.api_key)
    for dataset_id in dataset_ids:
        download_dataset(sm, dataset_id, p)


if __name__ == '__main__':
    main()
