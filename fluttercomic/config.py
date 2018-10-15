from simpleutil.config import cfg


def list_server_opts():
    from simpleservice.ormdb.config import database_opts
    from goperation.manager.wsgi.config import route_opts
    from fluttercomic.api.wsgi.config import comic_opts
    from fluttercomic.plugin.platforms.config import platforms_opts
    # from fluttercomic.api.wsgi.config import resource_opts
    cfg.set_defaults(route_opts,
                     routes=['fluttercomic.api.wsgi.routers.private'],
                     publics=['fluttercomic.api.wsgi.routers.public',
                              'fluttercomic.plugin.platforms.routers'])
    # return route_opts + resource_opts + database_opts
    return route_opts + comic_opts + platforms_opts + database_opts