#! /usr/bin/python
import socket
import struct
import sys, getopt	# for reading command line parameter

SPINN_SEND_TEMP	= 1
DEF_HOST = '192.168.240.253'
DEF_SEND_PORT = 17893 #tidak bisa diganti dengan yang lain
DEF_SDP_PORT = 7
DEF_SDP_CORE = 17
DEF_WITH_REPLY = 0x87
DEF_NO_REPLY = 0x07
DEF_SDP_IPTAG = 2
HOST_SEND_TERMINATE = 0xFFFF
HOST_SET_CHANGE_PLL = 2
HOST_REQ_REVERT_PLL = 3
HOST_SET_FREQ_VALUE = 4
HOST_REQ_FREQ_VALUE = 5
HOST_SEND_START_REPORT = 7
HOST_SEND_STOP_REPORT = 8
SPINN_SEND_REPORT = 10

def readCLI(argv):
   chipX = 0
   chipY = 0
   try:
      opts, args = getopt.getopt(argv,"hx:y:",["chipX=","chipY="])
   except getopt.GetoptError:
      print 'stopTempStream.py -x <chipX> -y <chipY>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
	 print 'stopTempStream.py -x <chipX> -y <chipY>'
	 print 'if x and y are not given, then chip<0,0> will be targeted'
	 sys.exit()
      elif opt in ("-x", "--chipX"):
	 chipX = int(arg)
      elif opt in ("-y", "--chipY"):
	 chipY = int(arg)
   return chipX, chipY

def sendSDP(sock, flags, tag, dp, dc, dax, day, cmd, seq, arg1, arg2, arg3, bArray):
    """
    The detail experiment with sendSDP() see mySDPinger.py
    """
    da = (dax << 8) + day
    dpc = (dp << 5) + dc
    sa = 0
    spc = 255
    pad = struct.pack('2B',0,0)
    hdr = struct.pack('4B2H',flags,tag,dpc,spc,da,sa)
    scp = struct.pack('2H3I',cmd,seq,arg1,arg2,arg3)
    if bArray is not None:
	sdp = pad + hdr + scp + bArray
    else:
	sdp = pad + hdr + scp
    HOST, PORT = DEF_HOST, DEF_SEND_PORT
    sock.sendto(sdp,(HOST,PORT))
    return sdp

def sendStart(sock, destChipX, destChipY):
    flags = DEF_NO_REPLY
    tag = DEF_SDP_IPTAG
    dp = DEF_SDP_PORT
    dc = DEF_SDP_CORE
    dax = destChipX
    day = destChipY
    cmd = HOST_SEND_START_REPORT
    seq = 0
    arg1 = 0
    arg2 = 0
    arg3 = 0
    bArray = None
    sendSDP(sock, flags, tag, dp, dc, dax, day, cmd, seq, arg1, arg2, arg3, bArray)

def main():
    udpSocketOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cX, cY = readCLI(sys.argv[1:])
    sendStart(udpSocketOut, cX, cY)
    udpSocketOut.close()
    
if __name__=='__main__':
    main()
    
