from simpleutil.config import cfg
from simpleservice.ormdb.config import database_opts

CONF = cfg.CONF


comic_opts = [
    cfg.StrOpt('basedir',
               default='/data/www/fluttercomic',
               help='Comic file base dir'),
    cfg.MultiOpt('ports_range',
                 item_type=cfg.types.PortRange(),
                 help='Websocket ports range in wsgi server'),
    cfg.StrOpt('user',
               help='Websocket upload process user'),
    cfg.StrOpt('group',
               help='Websocket upload process group'),
    cfg.StrOpt('ipaddr',
               help='Websocket upload ipaddr'
               ),
]


def register_opts(group):
    # database for gopdb
    CONF.register_opts(comic_opts, group)
    CONF.register_opts(database_opts, group)
