from simpleutil.config import cfg
from simpleutil.utils import attributes

from fluttercomic import common

CONF = cfg.CONF
conf = CONF[common.NAME]

WSPORTS = set([])

for p_range in attributes.validators['type:ports_range_list'](conf.ports_range) if conf.ports_range else []:
    down, up = map(int, p_range.split('-'))
    if down < 1024:
        raise ValueError('Port 1-1024 is not allowed')
    for port in xrange(down, up):
        WSPORTS.add(port)
