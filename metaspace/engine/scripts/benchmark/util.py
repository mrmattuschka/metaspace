import json
from pathlib import Path

import requests

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


def submit_dataset(sm, dataset_id, database_ids, p):
    is_public = False
    with open(p / dataset_id / 'metadata.json', 'r') as f:
        metadata = json.loads(f.read())

    directory = p / dataset_id
    names = set(
        x.stem for x in Path(directory).iterdir() if x.is_file() and x.suffix in ('.ibd', '.imzML')
    )
    for name in list(names):
        dataset_id = sm.submit_dataset(
            directory / Path(f'{name}.imzML'),
            directory / Path(f'{name}.ibd'),
            name,
            json.dumps(metadata),
            is_public,
            database_ids,
        )
        print(f'Submited dataset: {dataset_id}')
