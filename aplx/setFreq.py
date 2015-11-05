#! /usr/bin/python
import socket
import struct
import sys, getopt	# for reading command line parameter

SPINN_SEND_TEMP	= 1
DEF_HOST = '192.168.240.253'
DEF_SEND_PORT = 17893 #tidak bisa diganti dengan yang lain
DEF_RECV_PORT = 20000 #sesuaikan dengan nilai yang dipakai oleh profiler.h
DEF_GENERIC_UDP_PORT = 20000
DEF_GENERIC_IPTAG = 2		# remember to put this value in ybug
DEF_REPORT_PORT = 20001
DEF_REPORT_IPTAG = 3
DEF_SDP_PORT = 7
DEF_SDP_CORE = 17
DEF_WITH_REPLY = 0x87
DEF_NO_REPLY = 0x07
DEF_SDP_IPTAG = 2
HOST_SET_CHANGE_PLL = 2
HOST_REQ_REVERT_PLL = 3
HOST_SET_FREQ_VALUE = 4
HOST_REQ_FREQ_VALUE = 5

PLL_MODE_ORG = 0
PLL_MODE_RTR_IN_PLL2 = 1
PLL_MODE_RTR_EQU_CPU = 2

PLL_mode = 0

def displayHelp():
    print 'Usage:'
    print '\tsetProfiler -h'
    print '\tsetProfiler -x <chipX> -y <chipY>'
    print '\tsetProfiler -p 0'
    print '\tsetProfiler -p <PLL_mode> -f <freqMHz>'
    print '\tsetProfiler -h -p <PLL_mode> -f <freqMHz> -x <chipX> -y <chipY>\n'
    print 'The first format is used for displaying this help information'
    print 'The second format is used to read chip setting'
    print 'The third format is used to reset chip setting into default one'
    print 'The fourth format is used to change frequency of chip <0,0>'
    print 'The fourth format is used to change frequency of chip <chipX,chipY>\n'
    print 'The valid frequency range is: 10-255'
    print 'The PLL_mode is:'
    print '0: use default setting (200MHz for cores, 133MHz for Router & SDRAM'
    print '1: set system AHB and router to use PLL2 (together with SDRAM) at 130MHz'
    print '2: set system AHB and router to use the same frequency as CPUs'

def readCLI(argv):
   freq = -1
   chipX = 0
   chipY = 0
   pll = -1
   try:
      opts, args = getopt.getopt(argv,"hp:f:x:y:",["pllMode","freq=","chipX=","chipY="])
   except getopt.GetoptError:
      displayHelp()
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
	 displayHelp()
	 sys.exit()
      elif opt in ("-p", "--pllMode"):
	 pll = int(arg)
      elif opt in ("-f", "--freq"):
	 freq = int(arg)
      elif opt in ("-x", "--chipX"):
	 chipX = int(arg)
      elif opt in ("-y", "--chipY"):
	 chipY = int(arg)
   return pll, freq, chipX, chipY

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

def sendFreq(sock, freq, destChipX, destChipY):
    print "Will change to {}MHz in chip<{},{}>".format(freq,destChipX,destChipY)
    flags = DEF_NO_REPLY
    tag = DEF_SDP_IPTAG
    dp = DEF_SDP_PORT
    dc = DEF_SDP_CORE
    dax = destChipX
    day = destChipY
    cmd = HOST_SET_FREQ_VALUE
    seq = freq
    arg1 = 0
    arg2 = 0
    arg3 = 0
    bArray = None
    sendSDP(sock, flags, tag, dp, dc, dax, day, cmd, seq, arg1, arg2, arg3, bArray)

def changePLL2(sock,mode,destChipX, destChipY):
    flags = DEF_NO_REPLY
    tag = DEF_SDP_IPTAG
    dp = DEF_SDP_PORT
    dc = DEF_SDP_CORE
    dax = destChipX
    day = destChipY
    cmd = HOST_SET_CHANGE_PLL
    seq = mode
    arg1 = 0
    arg2 = 0
    arg3 = 0
    bArray = None
    sendSDP(sock, flags, tag, dp, dc, dax, day, cmd, seq, arg1, arg2, arg3, bArray)

def getReplyFromBoard(sock,replyCode):
    result = False
    data = sock.recv(1024)    #bisa juga pakai recvfrom jika ingin tahu sumber pengirimnya
    fmt = "<HQ2H"
    pad, hdr, cmd, seq = struct.unpack(fmt, data)

    if cmd==replyCode:
	result = True
    return result


def get_FR_str(fr):
    str = ""
    if fr==0:
	str = "25-50 MHz"
    elif fr==1:
	str = "50-100 MHz"
    elif fr==2:
	str = "100-200 MHz"
    elif fr==3:
	str = "200-400 MHz"
    else:
	str = "unknown range"
    return str

def getFreq(sel, ns1, ns2, ms1, ms2, dv):
    num = 1.0		# if sel==0
    denum = 1.0
    if sel==1:
	num = ns1
	denum = ms2
    elif sel==2:
	num = ns2
	denum = ms2
    elif sel==3:
	num = 1.0
	denum = 4.0
    fSrc = 10.0
    val = (fSrc * num) / (denum * dv)
    return val

def selName(s):
    name = ""
    if s==0:
	name = "clk_in"
    elif s==1:
	name = "pll1_clk"
    elif s==2:
	name = "pll2_clk"
    elif s==3:
	name = "clk_in_div_4"
    else:
	name = "unknown src"
    return name

def getFreqFromBoard(sock, destChipX, destChipY):
    """
    Just copy from readPLL.c
    """
    flags = DEF_NO_REPLY
    tag = DEF_SDP_IPTAG
    dp = DEF_SDP_PORT
    dc = DEF_SDP_CORE
    dax = destChipX
    day = destChipY
    cmd = HOST_REQ_FREQ_VALUE
    seq = 0
    arg1 = 0
    arg2 = 0
    arg3 = 0
    bArray = None
    sendSDP(sock, flags, tag, dp, dc, dax, day, cmd, seq, arg1, arg2, arg3, bArray)
    data = sock.recv(1024)
    fmt = "<HQ2H3I"
    pad, hdr, cmd, seq, arg1, arg2, arg3 = struct.unpack(fmt, data)
    if cmd==HOST_REQ_FREQ_VALUE:
	r20 = arg1
	r21 = arg2
	r24 = arg3
	FR1 = (r20 >> 16) & 3;
	MS1 = (r20 >> 8) & 0x3F;
	NS1 = r20 & 0x3F;
	FR2 = (r21 >> 16) & 3;
	MS2 = (r21 >> 8) & 0x3F;
	NS2 = r21 & 0x3F;

	Sdiv = ((r24 >> 22) & 3) + 1;
	Sys_sel = (r24 >> 20) & 3;
	Rdiv = ((r24 >> 17) & 3) + 1;
	Rtr_sel = (r24 >> 15) & 3;
	Mdiv = ((r24 >> 12) & 3) + 1;
	Mem_sel = (r24 >> 10) & 3;
	Bdiv = ((r24 >> 7) & 3) + 1;
	Pb = (r24 >> 5) & 3;
	Adiv = ((r24 >> 2) & 3) + 1;
	Pa = r24 & 3;

	Sfreq = getFreq(Sys_sel, NS1, NS2, MS1, MS2, Sdiv);
	Rfreq = getFreq(Rtr_sel, NS1, NS2, MS1, MS2, Rdiv);
	Mfreq = getFreq(Mem_sel, NS1, NS2, MS1, MS2, Mdiv);
	Bfreq = getFreq(Pb,      NS1, NS2, MS1, MS2, Bdiv);
	Afreq = getFreq(Pa,      NS1, NS2, MS1, MS2, Adiv);

	print "************* CLOCK INFORMATION **************"
	print "Reading registers directly..."
	print "PLL-1"
	print "----------------------------"
	print "Frequency range         : {}".format(get_FR_str(FR1))
	print "Output clk divider      : {}".format(MS1)
	print "Input clk multiplier    : {}\n".format(NS1)

	print "PLL-2"
	print "----------------------------"
	print "Frequency range         : {}".format(get_FR_str(FR2))
	print "Output clk divider      : {}".format(MS2)
	print "Input clk multiplier    : {}\n".format(NS2)

	print "Multiplerxer"
	print "----------------------------"
	print "System AHB clk divisor  : {}".format(Sdiv)
	print "System AHB clk selector : {} ({})".format(Sys_sel, selName(Sys_sel))
	print "System AHB clk freq     : {} MHz".format(Sfreq)
	print "Router clk divisor      : {}".format(Rdiv)
	print "Router clk selector     : {} ({})".format(Rtr_sel, selName(Rtr_sel))
	print "Router clk freq         : {} MHz".format(Rfreq)
	print "SDRAM clk divisor       : {}".format(Mdiv)
	print "SDRAM clk selector      : {} ({})".format(Mem_sel, selName(Mem_sel))
	print "SDRAM clk freq          : {} MHz".format(Mfreq)
	print "CPU-B clk divisor       : {}".format(Bdiv)
	print "CPU-B clk selector      : {} ({})".format(Pb, selName(Pb))
	print "CPU-B clk freq          : {} MHz".format(Bfreq)
	print "CPU-A clk divisor       : {}".format(Adiv)
	print "CPU-A clk selector      : {} ({})".format(Pa, selName(Pa))
	print "CPU-A clk freq          : {} MHz".format(Afreq)
	print "**********************************************"

def main():
    udpSocketOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
	print 'Opening port-{}...'.format(DEF_GENERIC_UDP_PORT),
	udpSocketIn.bind(('', DEF_GENERIC_UDP_PORT))
    except OSError as msg:
	print "%s" % msg
	udpSockIn.close
	udpSockOut.close
	sys.exit(1)
    print 'done!'
    try:
	PLL_mode, freq, cX, cY = readCLI(sys.argv[1:])
	if freq==-1:
	    if PLL_mode>=0:
		# first, change to PLL2 for AHB and Router
		changePLL2(udpSocketOut,PLL_mode,cX, cY)
		# then wait until spinn send reply
		print 'change PLL command is sent, waiting for reply...',
		getReply = False
		while not getReply:
		    getReply = getReplyFromBoard(udpSocketIn,HOST_SET_CHANGE_PLL)
		print 'done!'
	    getFreqFromBoard(udpSocketIn, cX, cY)

	else:
	    if freq>=10 and freq<=255:
		if PLL_mode>=0:
		    # first, change to PLL2 for AHB and Router
		    changePLL2(udpSocketOut,PLL_mode,cX, cY)
		    print 'change PLL command is sent, waiting for reply...',
		    # then wait until spinn send reply
		    getReply = False
		    while not getReply:
			getReply = getReplyFromBoard(udpSocketIn,HOST_SET_CHANGE_PLL)
		    print 'done!'
		# then set the frequency
		sendFreq(udpSocketOut, freq, cX, cY)
		# then wait until spinn send reply
		print 'change frequency command is sent, waiting for reply...',
		getReply = False
		while not getReply:
		    getReply = getReplyFromBoard(udpSocketIn,HOST_SET_FREQ_VALUE)
		print 'done!'
		getFreqFromBoard(udpSocketIn, cX, cY)
	    else:
		print 'Invalid frequency range!'
    except KeyboardInterrupt:
	print "The new profile is cancelled!"
    udpSocketOut.close()
    udpSocketIn.close()
    
if __name__=='__main__':
    main()
    
