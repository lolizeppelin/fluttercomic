from simpleutil.config import cfg


def list_server_opts():
    from simpleservice.ormdb.config import database_opts
    from goperation.manager.wsgi.config import route_opts
    # from fluttercomic.api.wsgi.config import resource_opts
    cfg.set_defaults(route_opts,
                     routes=['fluttercomic.api.wsgi.private'],
                     publics=['fluttercomic.api.wsgi.public',
                              'fluttercomic.plugin.wsgi.platforms.routers'])
    # return route_opts + resource_opts + database_opts
    return route_opts + database_opts