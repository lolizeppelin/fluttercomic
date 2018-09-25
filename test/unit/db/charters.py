import contextlib
import mysql.connector
import msgpack


@contextlib.contextmanager
def _lower_conn(host, port, user, passwd, schema=None,
                raise_on_warnings=True):
    kwargs = dict(user=user, passwd=passwd, host=host, port=port,
                  raise_on_warnings=raise_on_warnings)
    if schema:
        kwargs['database'] = schema
    conn = mysql.connector.connect(**kwargs)
    try:
        yield conn
    except Exception as e:
        print e
        raise
    finally:
        conn.close()

host = '172.20.0.3'
port = 3304
user = 'root'
passwd = '111111'
schema = 'fluttercomic'




def newchapters(cid, chapters):
    last = len(chapters)
    chapters = msgpack.packb([[max, ''] for max in chapters ])
    with _lower_conn(host, port, user, passwd, schema) as conn:
        cursor = conn.cursor()
        cursor.execute('select * from comics where cid = %d' % cid)
        comics = cursor.fetchall()
        comic = comics[0]
        for v in comic:
            print v,
        print ''
        if not comics:
            raise ValueError('cid %d can not be found' % cid)
        sql = "update comics set last=%d, chapters='%s' where cid =%d" % (last, chapters, cid)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        print 'update comic success'


def main():
    cid = 8
    cps = [213]
    newchapters(cid, cps)

if __name__ == '__main__':
    main()



