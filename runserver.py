#-----------------------------------------------------------------------
# runserver.py
# author: batya stein
#-----------------------------------------------------------------------

from sys import argv, stderr, exit
import argparse
from app import app


def createArgs():
    parser = argparse.ArgumentParser(description='The registrar application', allow_abbrev=False)
    parser.add_argument('port', metavar='port', type=int, help='the port at which the server should listen', nargs=1)
    return parser


def main():
    try:
        namespace = vars(createArgs().parse_args())
    except Exception as e:
        print('{}: {}'.format(argv[0], e), file=stderr)
        exit(2)
    [port] = namespace['port']
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__=='__main__':
    main()
