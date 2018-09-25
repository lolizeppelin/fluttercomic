from simpleutil.config import cfg
from simpleservice.ormdb.config import database_opts

CONF = cfg.CONF


comic_opts = [
    cfg.StrOpt('basedir',
               default='/data/www/fluttercomic/cdn',
               help='Comic file base dir'),
    cfg.StrOpt('logdir',
               default='/data/www/fluttercomic/log',
               help='Comic log dir'),
    cfg.MultiOpt('ports_range',
                 item_type=cfg.types.PortRange(),
                 help='Websocket ports range in wsgi server'),
    cfg.StrOpt('tmpdir',
               default='/data/www/fluttercomic/compressed',
               help='Comic compressed files local path'),
]



def register_opts(group):
    # database for gopdb
    CONF.register_opts(comic_opts, group)
    CONF.register_opts(database_opts, group)
