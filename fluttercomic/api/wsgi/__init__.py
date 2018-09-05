from simpleutil.config import cfg
from fluttercomic.api.wsgi.config import register_opts

from fluttercomic import common

CONF = cfg.CONF

register_opts(CONF.find_group(common.NAME))
