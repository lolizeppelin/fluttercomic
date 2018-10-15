from simpleutil.config import cfg

from fluttercomic import common
from fluttercomic.plugin.platforms.config import register_opts


CONF = cfg.CONF

group = CONF.find_group(common.NAME)
register_opts(group)
