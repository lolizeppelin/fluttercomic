import msgpack


def format_chapters(point, chapters, payed=None):
    payed = set(msgpack.unpackb(payed) if payed else [])
    chapters = msgpack.unpackb(chapters)
    return [dict(index=index+1,
                 max=c[0],
                 key=c[1] if (index < point or index in payed) else '')
            for index, c in enumerate(chapters)]
