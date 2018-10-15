import os
from goperation.cmd.server import wsgi

def main():
    basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../etc'))
    configs = [
        os.path.join(basepath, 'goperation.conf'),
        os.path.join(basepath, 'gcenter.conf')
    ]

    edir = os.path.join(basepath, 'endpoints')
    wsgi.run('gcenter-wsgi', configs, edir)


if __name__ == '__main__':

    print
    # main()
