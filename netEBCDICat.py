#!/usr/bin/env python3

#########################################################################
#			     netEBCDICat  re-written for python3
#########################################################################
# Script to communicate with netcat on OMVS (z/OS IBM Mainframe UNIX)
#
# Requirements: Python, netcat-omvs running on a mainframe
# Created by: Soldier of Fortran (@mainframed767)
# Usage: This script will listen for or connect to a z/OS OMVS
# mainframe netcat session and translate the data from
# UTF-8 to EBCDIC and back
#
# Copyright GPL 2019
###
# # Lots of help from http://4thmouse.com/index.php/2008/02/22/netcat-clone-in-three-languages-part-ii-python/
###
# To access other code pages install https://pypi.org/project/ebcdic/

from select import select
import socket
import signal
import sys
import argparse #needed for argument parsing
import logging
#for ebcdic
try:
  import ebcdic
  default_encoding = "cp1047"
except ImportError:
  default_encoding = "cp037"



# catch the ctrl-c to exit and say something instead of Punt!
def signal_handler(signal, frame):
        print('End of Line')
        sys.exit(0)


def main():
    version = "2.0"
    newline = 0x15
    signal.signal(signal.SIGINT, signal_handler)

    desc = '''
               __
              / _)
     _.----._/ /      netEBDICat.py
    /         /       by Soldier of FORTRAN
 __/ (  | (  |        v2 2019
/__.-'|_|--|_|

Script to communicate with z/OS IBM Mainframe who only speak EBCDIC 

'''


    parser = argparse.ArgumentParser(description=desc,
                                    epilog='Damn you EBCDIC!\n\nExample:\n ./netEBCDICat.py -e cp500 -l 54321\n ./netEBCDICat.py -d 1.1.0.1 12345',
                                    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-d', '--debug',
                        help="Print lots of debugging statements",
                        action="store_const",
                        dest="loglevel",
                        const=logging.DEBUG,
                        default=logging.WARNING)
    parser.add_argument('-v', '--verbose', 
                        help="Be verbose", 
                        action="store_const", 
                        dest="loglevel", 
                        const=logging.INFO)
    parser.add_argument('-c', '--codepage', 
                        help="EBCDIC code page. To access all code pages install https://pypi.org/project/ebcdic/ (Default cp037)", 
                        default=default_encoding)
    listen_or_ip = parser.add_mutually_exclusive_group(required=True)
    listen_or_ip.add_argument('-l','--listen',
                        help='listen for incomming connections', 
                        default=False,
                        dest='listen',
                        action='store_true')
    listen_or_ip.add_argument('ip', 
                        help='remote host IP address',
                        nargs='?')
    parser.add_argument('port', 
                        help='Port to listen on or to connect to')

    args = parser.parse_args()	

    logging.basicConfig(level=args.loglevel, format='netEBCDICat:%(levelname)s:%(message)s')
    logging.info("netEBCDICat version {}".format(version))
    logging.debug(args)

    logging.info("EBCDIC code page: {}".format(args.codepage))
    
    try:
        if args.listen:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("0.0.0.0", int(args.port))) 
            server.listen(1)
            logging.info("Listening on 0.0.0.0:{}".format(args.port))
            MFsock, address = server.accept()
            logging.info('Connection from {}:{}'.format(address[0],address[1]))
        else:
            logging.info("Connecting to {}:{}".format(args.ip,args.port))
            MFsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            MFsock.connect( (args.ip, int(args.port)) )
            logging.debug("Connected to {}:{}".format(args.ip,args.port))
    except Exception as e:
           logging.critical("Error: {}".format(e))
           sys.exit(0)
    
    MFsock.setblocking(0)
    while(1):
        r, w, e = select(
            [MFsock, sys.stdin], 
            [], 
            [MFsock, sys.stdin])
        try:
            size = 1024
            data = MFsock.recv(size)
            while( len(data) > 0 ):
                logging.debug("recv ({})\t {}".format(len(data), data.hex()))
                print(data.decode(args.codepage), end = '',  flush=True)
                data = MFsock.recv(size)
                if( len(data) > 0 ):
                    break
        except socket.error as e:
            pass

        while(1):
            r, w, e = select([sys.stdin],[],[],0)
            if(len(r) == 0):
                break
            c = input()
            if(c == ''):
                break
            logging.debug("send ({})\t {}".format(len(c+' '), c.encode(args.codepage).hex()))
            if(MFsock.sendall(c.encode(args.codepage)+b'\x15') != None):
                break   

main()
