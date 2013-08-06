# Copyright 2012 Omniscale (http://omniscale.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import json

import shapely

import logging
log = logging.getLogger(__name__)

from imposm import config
from imposm.mapping import Mapping

from pymongo import MongoClient

class MongoDB(object):
    insert_data_format = 'tuple'

    def __init__(self, db_conf):
        self.db_conf = db_conf
        self.srid = int(db_conf['proj'].split(':')[1])
        self._insert_stmts = {}
        self._connection = None

    @property
    def table_prefix(self):
        return self.db_conf.prefix.rstrip('_') + '_'

    def to_tablename(self, name):
        return self.table_prefix + name.lower()

    def is_postgis_2(self):
        pass

    @property
    def connection(self):
        if not self._connection:
            self.db_conf.port = int(self.db_conf.port)
            # todo username / password
            # todo ssl
            # test = self.db_conf.user+":"+self.db_conf.password+"@"
            mongo_client = MongoClient(self.db_conf.host, self.db_conf.port)
            self._connection = mongo_client[self.db_conf.db]
        return self._connection

    def commit(self):
        # There are not commits in MongoDB
        pass

    def insert(self, mapping, insert_data):
        tablename = self.table_prefix + mapping.name
        if mapping.fields:
            extra_arg_names = ['osm_id', 'geometry']
            extra_arg_names.extend([n for n, t in mapping.fields])

        for row in insert_data:
            insert_dict = []
            for elem in row:
                insert_dict.append(elem)
            dictionary = dict(zip(extra_arg_names, insert_dict))
            self.connection[tablename].insert(dictionary)

    def geom_wrapper(self, geom):
        return shapely.geometry.mapping(geom)

    def reconnect(self):
        self._connection = None
        self._cur = None

    def post_insert(self, mappings):
        mappings = [m for m in mappings if isinstance(m, (Mapping))]
        for mapping in mappings:
            tablename = self.to_tablename(mapping.name)
            self.connection[tablename].ensure_index( { "locs": "2d" } )

    def create_tables(self, mappings):
        for mapping in mappings:
            self.create_table(mapping)

    def create_table(self, mapping):
        tablename = self.to_tablename(mapping.name)

        # drop collection
        self.connection[tablename].drop()

        # # table in mongodb is collection
        self.connection.create_collection(tablename)

    def spatial_fun(self, mapping_names):
        pass

    def swap_tables(self, new_prefix, existing_prefix, backup_prefix):
        collections_names = self.connection.collection_names()
        system_collection = 'system.indexes'

        new_tables = False
        for collection_name in collections_names:
            if collection_name.startswith(new_prefix):
                new_tables = True;

        if not new_tables:
            raise RuntimeError('did not found tables to swap')

        # remove backup tables
        self.remove_tables(backup_prefix)

        # rename existing to backup
        existing_tables = []
        for collection_name in collections_names:
            if collection_name.startswith(existing_prefix) and not collection_name.startswith((new_prefix, backup_prefix)):
                existing_tables.append(collection_name)

        for collection_name in existing_tables:
            rename_to = collection_name.replace(existing_prefix, backup_prefix)
            self.connection[collection_name].rename(rename_to)

        # rename new to existing
        for collection_name in collections_names:
            if collection_name != system_collection and collection_name.startswith(new_prefix):
                rename_to = collection_name.replace(new_prefix, existing_prefix)
                self.connection[collection_name].rename(rename_to)


    def remove_tables(self, prefix):
        collection_names = self.connection.collection_names()
        for collection_name in collection_names:
            if collection_name.startswith(prefix):
                self.connection[collection_name].drop()

    def remove_views(self, prefix):
        # no views in mongodb
        pass

    def create_views(self, mappings, ignore_errors=False):
        # no views in mongodb
        pass

    def create_generalized_tables(self, mappings):
        # no views in mongodb
        pass

    def postprocess_tables(self, mappings):
        pass

    def optimize(self, mappings):
        raise NotImplementedError()

    def optimize_table(self, table_name, idx_name):
        raise NotImplementedError()

    def vacuum(self):
        raise NotImplementedError()
