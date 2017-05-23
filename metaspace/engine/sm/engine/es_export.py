from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError
from elasticsearch.client import IndicesClient
import logging

from sm.engine.util import SMConfig
from sm.engine.db import DB

logger = logging.getLogger('sm-engine')

COLUMNS = ["ds_id", "ds_name", "sf", "sf_adduct",
           "chaos", "image_corr", "pattern_match", "total_iso_ints", "min_iso_ints", "max_iso_ints", "msm",
           "adduct", "job_id", "sf_id", "fdr",
           "centroid_mzs", "ds_config", "ds_meta", "ion_image_url", "iso_image_urls", "polarity"]

ANNOTATIONS_SEL = '''
SELECT
    ds.id as ds_id,
    ds.name AS ds_name,
    f.sf,
    CONCAT(f.sf, m.adduct) as sf_adduct,
    --f.names AS comp_names,
    --f.subst_ids AS comp_ids,
    COALESCE(((m.stats -> 'chaos'::text)::text)::real, 0::real) AS chaos,
    COALESCE(((m.stats -> 'spatial'::text)::text)::real, 0::real) AS image_corr,
    COALESCE(((m.stats -> 'spectral'::text)::text)::real, 0::real) AS pattern_match,
    (m.stats -> 'total_iso_ints'::text) AS total_iso_ints,
    (m.stats -> 'min_iso_ints'::text) AS min_iso_ints,
    (m.stats -> 'max_iso_ints'::text) AS max_iso_ints,
    COALESCE(m.msm, 0::real) AS msm,
    m.adduct,
    j.id AS job_id,
    f.id AS sf_id,
    m.fdr as pass_fdr,
    tp.centr_mzs AS centroid_mzs,
    ds.config as ds_config,
    ds.metadata as ds_meta,
    m.ion_image_url,
    m.iso_image_urls,
    ds.config->'isotope_generation'->'charge'->'polarity' as polarity
FROM iso_image_metrics m
JOIN sum_formula f ON f.id = m.sf_id
JOIN job j ON j.id = m.job_id
JOIN dataset ds ON ds.id = j.ds_id
JOIN theor_peaks tp ON tp.sf = f.sf AND tp.adduct = m.adduct
	AND tp.sigma::real = (ds.config->'isotope_generation'->>'isocalc_sigma')::real
	AND tp.charge = (CASE WHEN ds.config->'isotope_generation'->'charge'->>'polarity' = '+' THEN 1 ELSE -1 END)
	AND tp.pts_per_mz = (ds.config->'isotope_generation'->>'isocalc_pts_per_mz')::int
WHERE ds.id = %s AND m.db_id = %s
ORDER BY COALESCE(m.msm, 0::real) DESC
'''


def init_es_conn(es_config):
    hosts = [{"host": es_config['host'], "port": int(es_config['port'])}]
    http_auth = (es_config['user'], es_config['password']) if 'user' in es_config else None
    return Elasticsearch(hosts=hosts, http_auth=http_auth)


class ESIndexManager(object):
    def __init__(self, es_config):
        self._es = init_es_conn(es_config)
        self._ind_client = IndicesClient(self._es)

    def internal_index_name(self, alias):
        yin, yang = '{}-yin'.format(alias), '{}-yang'.format(alias)
        assert not (self.exists_index(yin) and self.exists_index(yang)), \
            'Only one of {} and {} should exist'.format(yin, yang)

        if self.exists_index(yin):
            return yin
        elif self.exists_index(yang):
            return yang
        else:
            return yin

    def create_index(self, index):
        body = {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "max_result_window": 2147483647,
                    "analysis": {
                        "analyzer": {
                            "analyzer_keyword": {
                                "tokenizer": "keyword",
                                "filter": "lowercase"}}}}},
            "mappings": {
                "annotation": {
                    "dynamic_templates": [{
                        "strings": {
                            "match_mapping_type": "string",
                            "mapping": {
                                "type": "keyword"}}}],
                    "properties": {
                        "ds_id": {"type": "keyword"},
                        "comp_names": {
                            "type": "text",
                            "analyzer": "analyzer_keyword"},
                        "chaos": {"type": "float"},
                        "image_corr": {"type": "float"},
                        "pattern_match": {"type": "float", },
                        "total_iso_ints": {"type": "float", },
                        "min_iso_ints": {"type": "float", },
                        "max_iso_ints": {"type": "float"},
                        "msm": {"type": "float"},
                        "fdr": {"type": "float"}}}}}

        if not self._ind_client.exists(index):
            out = self._ind_client.create(index=index, body=body)
            logger.info('Index {} created\n{}'.format(index, out))
        else:
            logger.info('Index {} already exists'.format(index))

    def delete_index(self, index):
        if self._ind_client.exists(index):
            out = self._ind_client.delete(index)
            logger.info('Index {} deleted\n{}'.format(index, out))

    def exists_index(self, index):
        return self._ind_client.exists(index)

    def another_index_name(self, index):
        assert index.endswith('yin') or index.endswith('yang')

        if index.endswith('yin'):
            return index.replace('yin', 'yang')
        else:
            return index.replace('yang', 'yin')

    def remap_alias(self, new_index, alias='sm'):
        old_index = self.another_index_name(new_index)
        logger.info('Remapping {} alias: {} -> {}'.format(alias, old_index, new_index))

        self._ind_client.update_aliases({
            "actions": [{"add": {"index": new_index, "alias": alias}}]
        })
        if self._ind_client.exists_alias(old_index, alias):
            self._ind_client.update_aliases({
                "actions": [{"remove": {"index": old_index, "alias": alias}}]
            })
            out = self._ind_client.delete(index=old_index)
            logger.info('Index {} deleted:\n{}'.format(old_index, out))


class ESExporter(object):
    def __init__(self, es_config=None):
        if not es_config:
            es_config = SMConfig.get_conf()['elasticsearch']
        self._es = init_es_conn(es_config)
        self._db = DB(SMConfig.get_conf()['db'])
        self.index = es_config['index']

    def index_ds(self, ds_id, mol_db, del_first=False):
        if del_first:
            self.delete_ds(ds_id, mol_db)

        annotations = self._db.select(ANNOTATIONS_SEL, ds_id, mol_db.id)
        logger.info('Indexing {} documents: {}'.format(len(annotations), ds_id))

        n = 100
        to_index = []
        for r in annotations:
            d = dict(zip(COLUMNS, r))
            df = mol_db.get_molecules(d['sf'])
            d['db_name'] = mol_db.name
            d['db_version'] = mol_db.version
            d['comp_ids'] = df.mol_id.values.tolist()[:50]  # to prevent ES 413 Request Entity Too Large error
            d['comp_names'] = df.mol_name.values.tolist()[:50]
            d['centroid_mzs'] = ['{:010.4f}'.format(mz) if mz else '' for mz in d['centroid_mzs']]
            d['mz'] = d['centroid_mzs'][0]
            d['ion_add_pol'] = '[M{}]{}'.format(d['adduct'], d['polarity'])

            add_str = d['adduct'].replace('+', 'plus_').replace('-', 'minus_')
            to_index.append({
                '_index': self.index,
                '_type': 'annotation',
                '_id': '{}_{}_{}_{}_{}'.format(d['ds_id'], mol_db.name, mol_db.version,
                                               d['sf'], add_str),
                '_source': d
            })

            if len(to_index) >= n:
                bulk(self._es, actions=to_index, timeout='60s')
                to_index = []

        bulk(self._es, actions=to_index, timeout='60s')

    # TODO: add a test
    def delete_ds(self, ds_id, mol_db=None):
        must = [{'term': {'ds_id': ds_id}}]
        if mol_db:
            must.append({'term': {'db_name': mol_db.name}})
            must.append({'term': {'db_version': mol_db.version}})
        body = {
            'query': {
                'constant_score': {
                    'filter': {
                        'bool': {'must': must}}}}
        }
        res = self._es.search(index=self.index, body=body, _source=False, size=10 ** 9)['hits']['hits']
        to_del = [{'_op_type': 'delete', '_index': 'sm', '_type': 'annotation', '_id': d['_id']} for d in res]

        logger.info('Deleting %s documents from ES: %s, %s', len(to_del), ds_id, mol_db)

        del_n = 0
        try:
            del_n, _ = bulk(self._es, to_del, timeout='60s')
        except BulkIndexError as e:
            logger.warning('{} - {}'.format(e.args[0], e.args[1][1]))
        return del_n
