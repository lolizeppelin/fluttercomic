import msgpack


def format_chapters(point, chapters, payed=0):

    chapters = msgpack.unpackb(chapters)
    return [dict(index=index+1,
                 max=c[0],
                 key=c[1] if (index+1 < point or index+1 <= payed) else '')
            for index, c in enumerate(chapters)]