import argparse
from pathlib import Path

from metaspace import SMInstance

from util import (
    download_dataset,
    download_file,
    get_dataset_ids_from_csv_file,
    envs,
    submit_dataset,
)


def main():
    help_msg = 'Download datasets from one env and submit to another.'
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument(
        '--datasets_file',
        type=str,
        required=True,
        help='Path to file that contains dataset_ids in CSV format',
    )
    parser.add_argument(
        '--env_from',
        type=str,
        choices=envs.keys(),
        required=True,
        help='The name of the environment from which the dataset files will be downloaded.',
    )
    parser.add_argument(
        '--env_to',
        type=str,
        choices=envs.keys(),
        required=True,
        help='The name of the environment to which the dataset files will be submitted.',
    )
    parser.add_argument(
        '--api_key_from',
        type=str,
        required=True,
        help='API KEY of the environment from which the files will be downloaded.',
    )
    parser.add_argument(
        '--api_key_to',
        type=str,
        required=True,
        help='API KEY of the environment to which the files will be submitted.',
    )
    parser.add_argument('--database_ids', nargs='+', required=True, help='List of database ID.')
    args = parser.parse_args()

    dataset_ids = get_dataset_ids_from_csv_file(args.datasets_file)

    p = Path('.')
    sm_from = SMInstance(host=envs[args.env_from], api_key=args.api_key_from)
    sm_to = SMInstance(host=envs[args.env_to], api_key=args.api_key_to)
    for dataset_id in dataset_ids:
        download_dataset(sm_from, dataset_id, p)
        submit_dataset(sm_to, dataset_id, args.database_ids, p)


if __name__ == '__main__':
    main()
