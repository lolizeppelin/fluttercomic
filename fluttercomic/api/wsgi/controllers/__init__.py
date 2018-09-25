from simpleutil.config import cfg
from simpleutil.utils import attributes

from fluttercomic.api.wsgi.config import register_opts

from fluttercomic import common

CONF = cfg.CONF

register_opts(CONF.find_group(common.NAME))

conf = CONF[common.NAME]

WSPORTS = attributes.validators['type:ports_range_list'](conf.ports_range) if conf.ports_range else []
