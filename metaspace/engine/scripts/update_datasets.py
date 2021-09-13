import argparse
import json
from pathlib import Path

import requests
from metaspace import SMInstance

envs = {
    'beta': 'https://beta.metaspace2020.eu',
    'staging': 'https://staging.metaspace2020.eu',
    'prod': 'https://metaspace2020.eu',
}


def get_dataset_ids_from_csv_file(filename):
    with open(filename, 'r') as f:
        datasets = [d.strip('\n') for d in f.readlines()]
    return datasets


def check_db_ids(sm, ids):
    database_ids = [str(db.id) for db in sm.databases()]
    nonexistence = [_id for _id in ids if _id not in database_ids]
    return nonexistence


def main():
    help_msg = 'Update the datasets databases.\n'
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
    parser.add_argument('--database_ids', nargs='+', required=True, help='List of database ID.')
    args = parser.parse_args()

    dataset_ids = get_dataset_ids_from_csv_file(args.datasets_file)

    p = Path('.')
    sm = SMInstance(host=envs[args.env], api_key=args.api_key)

    nonexistence = check_db_ids(sm, args.database_ids)
    if nonexistence:
        msg = 'Molecular databases with IDs: {} do not exist'.format(', '.join(nonexistence))
        raise Exception(msg)

    for dataset_id in dataset_ids:
        ds = sm.dataset(id=dataset_id)
        sm.update_dataset_dbs(dataset_id, args.database_ids, ds.adducts)


if __name__ == '__main__':
    main()
