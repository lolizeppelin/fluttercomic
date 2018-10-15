from fluttercomic.cmd.db.utils import init_fluttercomic

dst = {'host': '192.168.191.2',
       'port': 3306,
       'schema': 'fluttercomic',
       'user': 'root',
       'passwd': '111111'}

init_fluttercomic(dst)