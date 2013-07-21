# Copyright 2011 Omniscale (http://omniscale.com)
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

import re
import os
import tempfile
import shutil

from contextlib import contextmanager

import imposm.app
import imposm.db.config
import imposm.mapping

from nose.tools import eq_
from nose.plugins import skip

temp_dir = None
old_cwd = None

try:
    from imposm_test_conf import db_conf
    db_conf = imposm.mapping.Options(db_conf)
except ImportError:
    raise skip.SkipTest('no imposm_test_conf.py with db_conf found')

def setup_module():
    global old_cwd, temp_dir
    old_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    test_osm_file = os.path.join(os.path.dirname(__file__), 'test.out.osm')
    with capture_out():
        imposm.app.main(['--read', test_osm_file, '--write', '--database', db_conf.db, 
            '--host', 'localhost', '--port', 27017,
            '--proj', db_conf.proj, '--table-prefix', db_conf.prefix])

class TestImportedMongoDB(object):
    def __init__(self):
        self.db = imposm.db.config.DB(db_conf)
        self.db.connection[db_conf.db]        # self.db.connection()

    def test_point(self):
        tablename = db_conf.prefix+'places'
        result = self.db.connection[tablename].find_one({'osm_id': 1})
        eq_(result['osm_id'], 1)
        eq_(result['name'], 'Foo')
        eq_(result['geometry']['type'], 'Point')
        eq_(result['geometry']['coordinates'], [13.0, 47.5])
        

    def test_way(self):
        tablename = db_conf.prefix+'landusages'
        result = self.db.connection[tablename].find_one({'osm_id': 1001})
        eq_(result['osm_id'], 1001)
        eq_(result['name'], 'way 1001')
        eq_(result['type'], 'wood')
        eq_(result['geometry']['type'], 'Polygon')
        eq_(result['geometry']['coordinates'], [[[12.999999941167431, 47.499999988412014],[14.49999993593292, 49.9999999238085], [16.499999984832954, 48.99999998317753], [16.99999995514844, 46.9999999342775], [14.49999993593292, 45.49999993951201], [12.999999941167431, 47.499999988412014]], [[13.999999965617434, 47.499999988412014], [14.999999990067437, 46.9999999342775], [15.499999960382922, 47.9999999587275], [14.49999993593292, 48.499999929042986], [13.999999965617434, 47.499999988412014]]])

        result = self.db.connection[tablename].find_one({'osm_id': 2002})
        eq_(result['osm_id'], 2002)
        eq_(result['name'], 'way 2002')
        eq_(result['type'], 'wood')
        eq_(result['geometry']['type'], 'Polygon')
        eq_(result['geometry']['coordinates'], [[[24.199999963550454, 48.24999994388526], [24.69999993386594, 49.24999996833526], [25.699999958315942, 48.79999997828753], [25.249999968268213, 47.699999993302015], [24.199999963550454, 48.24999994388526]]])
        
        result = self.db.connection[tablename].find_one({'osm_id': 3001})


def teardown_module():
    if old_cwd:
        os.chdir(old_cwd)

    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@contextmanager
def capture_out():
    import sys
    from cStringIO import StringIO

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
