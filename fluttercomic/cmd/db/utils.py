from simpleservice.ormdb.tools.utils import init_database

from fluttercomic.models import TableBase


def init_fluttercomic(db_info):
    init_database(db_info, TableBase.metadata)
