"""Pure reviewed minimal activity catalog; no source reads, approval or writes.

Source hashes bind private original semantics. Public view hashes bind only the
fixed listing fields, and rights assertions cover only that exact projection.
"""
from __future__ import annotations

import copy
import re

from .activity_checkpoints import ActivityCheckpointError, validate_checkpoint
from .activity_public import (MAX_PUBLIC_BYTES, MAX_RIGHTS_BYTES, POLICY,
                              ActivityPublicError, _clock, _require,
                              activity_digest, canonical_activity_json)
from .park_activities import (MAX_RECORD_BYTES, MAX_RECORDS, MAX_SNAPSHOT_BYTES,
                              PILOT_CODES, SNAPSHOT_FIELDS, ActivityError,
                              _official_url, _text, validate_activities)

DISPOSITION_FIELDS = {'schema_version', 'purpose', 'checkpoint_id', 'reviewed_at', 'records'}
DISPOSITION_RECORD_FIELDS = {'park_code', 'activity_id', 'source_content_hash', 'decision', 'categories'}
SOURCE_RECORD_FIELDS = {'id', 'content_hash', 'hash_scope', 'observed_first_at',
                        'observed_changed_at', 'publication_status'}
CATALOG_RECORD_FIELDS = {'id', 'park_code', 'title', 'url', 'activity_categories', 'category_scope',
                         'geographic_relationship', 'responsible_agency', 'difficulty',
                         'permit_required', 'availability_status', 'source_updated_at',
                         'observed_first_at', 'observed_changed_at', 'source_content_hash',
                         'view_hash', 'hash_scope'}
CATALOG_RIGHTS_FIELDS = {'park_code', 'activity_id', 'source_url', 'source_content_hash', 'view_hash',
                         'classification', 'use_scope', 'third_party_material_reproduced',
                         'nps_marks_reproduced', 'media_reproduced'}


def _checkpoint(value: object) -> dict:
    try:
        return validate_checkpoint(value)
    except ActivityCheckpointError:
        raise ActivityPublicError('invalid_activity_public_checkpoint') from None


def _identifier(value: object) -> None:
    try:
        _text(value, identifier=True)
    except ActivityError:
        raise ActivityPublicError('invalid_activity_catalog_identifier') from None


def _hash(value: object) -> None:
    _require(type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None,
             'invalid_activity_catalog_hash')


def _plain(value: object) -> None:
    _require(type(value) is str and 0 < len(value) <= 1024 and bool(value.strip())
             and re.search(r'[\x00-\x1f\x7f-\x9f<>]', value) is None,
             'invalid_activity_catalog_text')


def _categories(value: object) -> None:
    if value is None:
        return
    _require(type(value) is list and len(value) <= 1000, 'invalid_activity_catalog_categories')
    ids = []
    for category in value:
        _require(type(category) is dict and set(category) == {'id', 'name'},
                 'invalid_activity_catalog_categories')
        _identifier(category['id'])
        _plain(category['name'])
        ids.append(category['id'])
    _require(ids == sorted(set(ids)), 'invalid_activity_catalog_categories')


def _view_hash(record: dict) -> str:
    return activity_digest({key: item for key, item in record.items()
                            if key not in ('view_hash', 'hash_scope')}, max_bytes=MAX_RECORD_BYTES)


def validate_dispositions(value: dict, checkpoint: dict) -> dict:
    """Require explicit ordered decisions for every original retained record."""
    source = _checkpoint(checkpoint)
    _require(type(value) is dict and set(value) == DISPOSITION_FIELDS,
             'invalid_activity_catalog_dispositions')
    _require(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['purpose'] == 'private_activity_catalog_dispositions'
             and value['checkpoint_id'] == source['checkpoint_id'],
             'invalid_activity_catalog_dispositions')
    _require(_clock(value['reviewed_at']) >= _clock(source['checked_at']),
             'activity_dispositions_review_predates_collection')
    originals = [(s['park_code'], r) for s in source['inventories'] for r in s['records']]
    _require(type(value['records']) is list and len(value['records']) == len(originals),
             'invalid_activity_catalog_dispositions_scope')
    for row, (code, record) in zip(value['records'], originals):
        _require(type(row) is dict and set(row) == DISPOSITION_RECORD_FIELDS,
                 'invalid_activity_catalog_dispositions_scope')
        _require(row['park_code'] == code and row['activity_id'] == record['id']
                 and row['source_content_hash'] == record['content_hash'],
                 'activity_dispositions_binding_mismatch')
        _require(type(row['decision']) is str and row['decision'] in ('selected', 'withheld')
                 and type(row['categories']) is str and row['categories'] in ('published', 'withheld')
                 and (row['decision'] != 'withheld' or row['categories'] == 'withheld'),
                 'invalid_activity_catalog_disposition')
    canonical_activity_json(value, max_bytes=MAX_PUBLIC_BYTES)
    return copy.deepcopy(value)


def project_catalog(checkpoint: dict, dispositions: dict) -> dict:
    """Copy only fixed selected listings; retain source identity for all rows."""
    source = _checkpoint(checkpoint)
    plan = validate_dispositions(dispositions, source)
    choices = iter(plan['records'])
    inventories = []
    for snapshot in source['inventories']:
        inventory = {key: copy.deepcopy(item) for key, item in snapshot.items() if key != 'records'}
        inventory.update(schema_version=2, records=[], source_records=[])
        for original in snapshot['records']:
            choice = next(choices)
            inventory['source_records'].append({key: original[key] for key in SOURCE_RECORD_FIELDS
                if key != 'publication_status'} | {'publication_status': choice['decision']})
            if choice['decision'] == 'withheld':
                continue
            record = {key: copy.deepcopy(original[key]) for key in
                ('id', 'park_code', 'title', 'url', 'geographic_relationship', 'responsible_agency',
                 'difficulty', 'permit_required', 'source_updated_at', 'observed_first_at', 'observed_changed_at')}
            record.update(activity_categories=copy.deepcopy(original['activity_categories'])
                          if choice['categories'] == 'published' else None,
                          category_scope=choice['categories'], availability_status='not_verified',
                          source_content_hash=original['content_hash'], hash_scope='catalog_view')
            record['view_hash'] = _view_hash(record)
            inventory['records'].append(record)
        inventories.append(inventory)
    return validate_catalog({'schema_version': 2, 'purpose': 'public_park_activities',
                             'inventories': inventories})


def _validate_inventory(snapshot: object, code: str, checked_at: str) -> None:
    _require(type(snapshot) is dict and set(snapshot) == SNAPSHOT_FIELDS | {'source_records'},
             'invalid_public_activity_inventory')
    _require(type(snapshot['schema_version']) is int and snapshot['schema_version'] == 2,
             'invalid_public_activity_inventory')
    header = {key: item for key, item in snapshot.items() if key != 'source_records'}
    header.update(schema_version=1, records=[])
    try:
        validate_activities(header)
    except ActivityError:
        raise ActivityPublicError('invalid_public_activity_inventory') from None
    _require(snapshot['park_code'] == code and snapshot['last_successful_fetch_at'] is not None
             and snapshot['last_checked_at'] == checked_at, 'invalid_public_activity_scope')
    successful = _clock(snapshot['last_successful_fetch_at'])
    sources, records = snapshot['source_records'], snapshot['records']
    _require(type(sources) is list and len(sources) <= MAX_RECORDS
             and type(records) is list and len(records) <= MAX_RECORDS, 'invalid_public_activity_inventory')
    selected = []
    ids = []
    for source in sources:
        _require(type(source) is dict and set(source) == SOURCE_RECORD_FIELDS,
                 'invalid_activity_catalog_source')
        _identifier(source['id'])
        _hash(source['content_hash'])
        _require(source['hash_scope'] == 'normalized_record'
                 and type(source['publication_status']) is str
                 and source['publication_status'] in ('selected', 'withheld'),
                 'invalid_activity_catalog_source')
        _require(_clock(source['observed_first_at']) <= _clock(source['observed_changed_at']) <= successful,
                 'invalid_activity_catalog_observation_clock')
        canonical_activity_json(source, max_bytes=MAX_RECORD_BYTES)
        ids.append(source['id'])
        if source['publication_status'] == 'selected':
            selected.append(source)
    _require(ids == sorted(set(ids)) and len(records) == len(selected), 'invalid_activity_catalog_selection')
    for record, source in zip(records, selected):
        _require(type(record) is dict and set(record) == CATALOG_RECORD_FIELDS,
                 'invalid_activity_catalog_record')
        _require(record['id'] == source['id'] and record['park_code'] == code
                 and record['source_content_hash'] == source['content_hash']
                 and all(record[field] == source[field] for field in ('observed_first_at', 'observed_changed_at')),
                 'activity_catalog_source_binding_mismatch')
        _plain(record['title'])
        try:
            _official_url(record['url'], {code}, global_activity=True)
        except ActivityError:
            raise ActivityPublicError('invalid_activity_catalog_url') from None
        _require('?' not in record['url'] and '#' not in record['url'], 'invalid_activity_catalog_url')
        _require(type(record['category_scope']) is str and record['category_scope'] in ('published', 'withheld')
                 and (record['category_scope'] != 'withheld' or record['activity_categories'] is None),
                 'invalid_activity_catalog_categories')
        _categories(record['activity_categories'])
        _require(record['geographic_relationship'] == 'unconfirmed'
                 and all(record[field] is None for field in
                         ('responsible_agency', 'difficulty', 'permit_required', 'source_updated_at'))
                 and record['availability_status'] == 'not_verified', 'unsupported_activity_catalog_interpretation')
        _require(record['hash_scope'] == 'catalog_view', 'invalid_activity_catalog_hash_scope')
        _hash(record['view_hash'])
        canonical_activity_json(record, max_bytes=MAX_RECORD_BYTES)
        _require(record['view_hash'] == _view_hash(record), 'activity_catalog_view_hash_mismatch')
    canonical_activity_json(snapshot, max_bytes=MAX_SNAPSHOT_BYTES)


def validate_catalog(value: dict) -> dict:
    """Validate the public subset without claiming to rehash private source text."""
    _require(type(value) is dict and set(value) == {'schema_version', 'purpose', 'inventories'})
    _require(type(value['schema_version']) is int and value['schema_version'] == 2
             and value['purpose'] == 'public_park_activities')
    rows = value['inventories']
    _require(type(rows) is list and len(rows) == len(PILOT_CODES), 'invalid_public_activity_scope')
    _require(type(rows[0]) is dict and 'last_checked_at' in rows[0], 'invalid_public_activity_inventory')
    for code, snapshot in zip(PILOT_CODES, rows):
        _validate_inventory(snapshot, code, rows[0]['last_checked_at'])
    canonical_activity_json(value, max_bytes=MAX_PUBLIC_BYTES)
    return copy.deepcopy(value)


def validate_catalog_rights(rights: dict, dataset: dict) -> dict:
    """Bind exact public strings and every source summary in the full projection."""
    catalog = validate_catalog(dataset)
    _require(type(rights) is dict and set(rights) == {
        'schema_version', 'purpose', 'reviewed_at', 'review_method', 'policy', 'records', 'projection_hash'},
        'invalid_activity_rights')
    _require(type(rights['schema_version']) is int and rights['schema_version'] == 2
             and rights['purpose'] == 'public_park_activity_text_rights'
             and rights['review_method'] == 'official_nps_policy_and_exact_activity_review',
             'invalid_activity_rights')
    reviewed = _clock(rights['reviewed_at'])
    policy = rights['policy']
    _require(type(policy) is dict and set(policy) == set(POLICY)
             and all(type(policy[key]) is type(expected) and policy[key] == expected
                     for key, expected in POLICY.items()), 'invalid_activity_rights_policy')
    _require(rights['projection_hash'] == activity_digest(catalog, max_bytes=MAX_PUBLIC_BYTES),
             'activity_rights_projection_binding_mismatch')
    rows = rights['records']
    _require(type(rows) is list and len(rows) == sum(len(s['records']) for s in catalog['inventories']),
             'invalid_activity_rights_scope')
    offset = 0
    for snapshot in catalog['inventories']:
        _require(reviewed >= _clock(snapshot['last_checked_at']), 'activity_rights_review_predates_collection')
        for record in snapshot['records']:
            row = rows[offset]
            offset += 1
            _require(type(row) is dict and set(row) == CATALOG_RIGHTS_FIELDS, 'invalid_activity_rights_scope')
            expected = {'park_code': snapshot['park_code'], 'activity_id': record['id'],
                        'source_url': snapshot['source_url'], 'source_content_hash': record['source_content_hash'],
                        'view_hash': record['view_hash'], 'classification': 'nps_government_text',
                        'use_scope': 'activity_catalog_title_url_and_optional_categories',
                        'third_party_material_reproduced': False, 'nps_marks_reproduced': False,
                        'media_reproduced': False}
            _require(all(type(row[key]) is type(item) and row[key] == item for key, item in expected.items()),
                     'activity_rights_binding_mismatch')
    canonical_activity_json(rights, max_bytes=MAX_RIGHTS_BYTES)
    return copy.deepcopy(rights)
