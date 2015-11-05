#! /usr/bin/python
import socket
import struct
import sys, getopt	# for reading command line parameter

DEF_PORT = 20001
DEF_IPTAG = 3
SPINN_SEND_TEMP	= 1
SPINN_SEND_REPORT = 10

fT = list()			# for temperature data
fI = list()			# for idle counter

def openPort():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        #parameter dari bind() adalah tupple dengan format: bind(address)
        sock.bind( ('', DEF_PORT) )     #'' sepertinya berarti HostAddress::Any
        #sock.bind( (None, DEF_PORT) )     #None seharusny berarti HostAddress::Any -> all available interface
    except OSError as msg:
        print "%s" % msg
        sock.close()
        sock = None
    return sock

def closePort(sock):
    sock.shutdown()
    sock.close()
#    return

def displayHelp():
    print 'readReport.py -h -n <numOfChip> -f <outputFile>'
    print 'will use port {} specified in iptag-{}'.format(DEF_PORT, DEF_IPTAG)

def readCLI(argv):
   if len(sys.argv) < 2:
       displayHelp()
       sys.exit(1)
   tempfile = None
   nFile = 0
   try:
      opts, args = getopt.getopt(argv,"hn:f:",["file=","nofchips"])
   except getopt.GetoptError:
      displayHelp()
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
	 displayHelp()
	 sys.exit()
      elif opt in ("-f", "--file"):
	 tempfile = arg
      elif opt in ("-n", "--nofchips"):
	 nFile = int(arg)
   return nFile, tempfile

def readPort(sock):
    """
    Remark on struct formating:
    H = unsigned short (integer) -> 2 byte
    B = unsigned char (integer)	-> 1 byte
    """
    global fT, fI
    data = sock.recv(1024)    #bisa juga pakai recvfrom jika ingin tahu sumber pengirimnya
    szSdpHdr = 8		#8 bytes for sdp header
    szCmdHdr = 16		#16 bytes for scp header
    szReport = 2+8+16+(4*18)	#pad, sdp_hdr, scp_hdr, payload
    print 'Receiving %d bytes' % len(data)
    if len(data)==szReport:
	fmt = "<HQ2H3I18I"
	pad, hdr, cmd, seq, temp1, temp2, temp3, cpu0, cpu1, cpu2, cpu3, cpu4, cpu5, cpu6, cpu7, cpu8, cpu9, cpu10, cpu11, cpu12, cpu13, cpu14, cpu15, cpu16, cpu17 = struct.unpack(fmt, data)

	if cmd==SPINN_SEND_REPORT:
	    #To write something other than a string, it needs to be converted to a string first:
	    tVal = "{},{},{},{}\n".format(seq, temp1, temp2, temp3)
	    iVal = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(seq, cpu0, cpu1, cpu2, cpu3, cpu4, cpu5, cpu6, cpu7, cpu8, cpu9, cpu10, cpu11, cpu12, cpu13, cpu14, cpu15, cpu16, cpu17)
	    sax = seq >> 8
	    say = seq & 0xFF

	    fT[sax*2+say].write(tVal)
	    fI[sax*2+say].write(iVal)
	    print "[{},{}] : {}\t{}\t{}\n".format(sax,say,temp1,temp2,temp3),


def main():
    """ Try to implement Tubotron for my own exercise
    """
    n, fName = readCLI(sys.argv[1:])
    print "n = {}".format(n)
    for i in range(n):
	fT.append(open(fName+'_temp.'+str(i), 'w'))
	fI.append(open(fName+'_idle.'+str(i), 'w'))

    print "Opening up UDP socket on port %d..." % DEF_PORT
    udpSocket = openPort()
    if udpSocket is None:
        print "Cannot open the socket!"
    else:
        while True:
            #print "Waiting..."
            try:
		readPort(udpSocket)
            except KeyboardInterrupt:
                break
        print "\nClosing the UDP port..."
        udpSocket.close()
	for i in range(n):
	    fT[i].close
	    fI[i].close

    print "Finished!"
    
if __name__=='__main__':
    main()
    
