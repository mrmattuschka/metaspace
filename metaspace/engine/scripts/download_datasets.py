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


def download_file(url, file_path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)


def download_dataset(sm, dataset_id, p):
    print(dataset_id)
    Path.mkdir(p / dataset_id, exist_ok=True)

    dataset_files = set(
        x.stem
        for x in Path(p / dataset_id).iterdir()
        if x.is_file() and x.suffix in ('.ibd', '.imzML')
    )
    if dataset_files:
        return

    ds = sm.dataset(id=dataset_id)
    database_ids = [db.id for db in ds.database_details]
    with open(p / dataset_id / 'database.json', 'w') as f:
        f.write(json.dumps({'database_ids': database_ids}))

    metadata = dict(ds.metadata)
    with open(p / dataset_id / 'metadata.json', 'w') as f:
        f.write(json.dumps(metadata))

    for file in ds.download_links()['files']:
        url = file['link']
        filename = file['filename'].lower()
        if 'imzml' in filename:
            filename = filename[:-2] + filename[-2:].upper()
        print(filename)
        download_file(url, p / dataset_id / filename)


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
        choices=urls.keys(),
        required=True,
        help='Name of environmetn: beta, staging, prod',
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
