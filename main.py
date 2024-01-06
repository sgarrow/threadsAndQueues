import threading
import queue
import time
import random
pad =  ' ' * 75
#############################################################################

def workFunc1(*args):

    myThrNme = args[0]
    x  = random.uniform(.01, 1.0)
    kElapsed = 0
    kStart = time.time()

    block = True
    block = False

    if block:
        time.sleep(x)
        print(' {} {}. Wrk: {:5.2f} sec.'.format(pad,myThrNme,x))
    else:
        while kElapsed < x:
            time.sleep(0.0001)
            kEnd = time.time()
            kElapsed = kEnd-kStart
        #print(' {} {}. Wrk: {:5.2f} {:5.2f} sec.'.format(pad,myThrNme,x,kElapsed))

    return x
#############################################################################

def aThreadWhileOneLoop(*args):
    myThrNum   = args[0]
    qDict      = args[1]
    lock       = args[2]
    numThreads = args[3]

    myCommandQ = qDict[myThrNum]['cq']
    myThrNme   = threading.current_thread().name

    global seqNum
     
    while(1):
        x  = random.uniform(.01, 1)
        time.sleep(x)

        try:                      # Look for a command. 
            cmd = myCommandQ.get(block = False)
        except queue.Empty:
            cmd = { 'cmd': None }
        else:
            print(' {} {}. Get: {}.'.format(pad, myThrNme, cmd), flush = True)

        if cmd['cmd'] == 'quit':  # Terminate command received?
            break

        elif cmd['cmd'] == 'cmdToDoWrk': # Some other command received?
                                  # If so, spend time doing work. 
            wrkRsp = '{:4.2f}'.format(workFunc1(myThrNme)) 

            toSend = { 'rspTo': cmd['cmdFrom'], 'rspFrom': myThrNum, 
                       'rsp':   wrkRsp, 'seqNum': cmd['seqNum'] }

            print(' {} {}. Put: {}.'.format(pad,myThrNme,toSend),flush=True)

            myRespondToQ = qDict[cmd['cmdFrom']]['rq']
            myRespondToQ.put(toSend)

        elif cmd['cmd'] == 'cmdToSndMsg': # Some other command received?
                                          # If so, spend time doing work.

            # Send a cmd to a random thread.
            wrkThrd2SendTo = random.randint(1, numThreads)
            #wrkThrd2SendTo = myThrNum
            secondCmd = 'cmdToDoWrk'
            toSend = { 'cmdTo': wrkThrd2SendTo, 'cmdFrom': myThrNum, 
                       'cmd': secondCmd, 'seqNum':seqNum }
            incSeqNum(lock)
            print(' {} {}. Put: {}.'.format(pad,myThrNme,toSend),flush=True)
            qDict[wrkThrd2SendTo]['cq'].put(toSend)

            ###  Send a response back to main ... then proceed. 
            wrkRsp = '{:4.2f}'.format(workFunc1(myThrNme))

            toSend = { 'rspTo': cmd['cmdFrom'], 'rspFrom': myThrNum, 
                       'rsp':   'sent', 'seqNum': cmd['seqNum'] }

            print(' {} {}. Put: {}.'.format(pad,myThrNme,toSend),flush=True)

            myRespondToQ = qDict[cmd['cmdFrom']]['rq']
            myRespondToQ.put(toSend)

        # Check for any responses that have been sento to other trhds via cmdToSndMsg
        try:
            cmdRsp = qDict[myThrNum]['rq'].get(block = False)
        except queue.Empty:
            cmdRsp = None
        else:
            print(' {} {}. Get: {}.'.format(pad, myThrNme, cmdRsp), flush = True)

    return 0
#############################################################################

def mainThread0(*args):
    return 0
#############################################################################

def incSeqNum(lock):
    global seqNum
    #seqNum += 1
    gotLock = lock.acquire(blocking = False)
    if gotLock:
        #print('gotLock')
        seqNum += 1
        lock.release()
    else:
        print('not gotLock')
#############################################################################


global seqNum # Modified by threads so protect with a lock.
if __name__ == '__main__':

    print('\n Main. Creating variables.')
    global seqNum
    seqNum = 0
    lock   = threading.Lock()

    numThreads    = 5
    numCmdsToSend = 10
    numExpRsp     = 10
    numRcvdRsp    = 0

    qDict         = {} # A place to hold all Q's for all threads (and main).
    tLst          = [] # List of functions to be passed to 'create thread'.
    mainThreadIdx = 0  # Threads numbered 1,2,... and 0 is reserved for main.
    #########################################################################

    print('\n Main. Creating message queues for \'main\' ands all threads.')
    # e.g. qDict[1][cq]: Where Thrd1 looks for cmds sent to it.
    #      qDict[1][rq]: Where Thrd1 looks for responses to cmds it.
    print('\n Main. Creating Queues.')
    for ii in range(numThreads+1):
        qDict[ii] = {'cq': queue.Queue(), 'rq': queue.Queue()}
    #########################################################################

    # Create all the threads.
    print(' Main. Creating worker threads.')
    for t in range(1,numThreads+1): # <- 1 RE: skip Dummy.
        tLst.append(threading.Thread(group  = None, 
                                     target = aThreadWhileOneLoop, 
                                     name   = 'Thr{}'.format(t),
                                     # Threads use t as its idx into qDict.
                                     args = (t, qDict, lock, numThreads),
                                     kwargs = {}, 
                                     daemon = None))
    #########################################################################

    # Start the threads.
    print(' Main. Starting worker threads.')
    for t in tLst:
        t.start()
    #########################################################################

    kStart        = time.time()
    print(' Main: Sending cmds to threads.\n')
    for ii in range(numCmdsToSend):

        # Send a cmd to a random thread.
        wrkThrd2SendTo = random.randint(1, len(tLst))
        cmdLst = ['cmdToDoWrk','cmdToSndMsg']
        cmd    = random.choice(cmdLst)
        #cmd = 'cmdToDoWrk'
        #cmd = 'cmdToSndMsg'
        toSend = { 'cmdTo': wrkThrd2SendTo, 'cmdFrom': mainThreadIdx, 
                   'cmd': cmd, 'seqNum':seqNum }
        incSeqNum(lock)
        print(' Main. Put: {}.'.format(toSend), flush = True)
        qDict[wrkThrd2SendTo]['cq'].put(toSend)

        # Check for any responses.
        try:
            cmdRsp = qDict[mainThreadIdx]['rq'].get(block = False)
        except queue.Empty:
            cmdRsp = None
        else:
            print(' Main. Get: {}.'.format(cmdRsp), flush = True)
            numRcvdRsp += 1
        
        time.sleep(random.uniform(.01, 1) ) # sleep before sending nxt cmd.
    #########################################################################

    print('\n Main: Waiting for all responses.')
    while numRcvdRsp < numExpRsp:
        try:
            cmdRsp = qDict[mainThreadIdx]['rq'].get(block = False)       
        except queue.Empty:
            continue
        else:
            print(' Main. Get: {}.'.format(cmdRsp), flush = True)
            numRcvdRsp += 1
    kEnd = time.time()
    kElapsed = kEnd-kStart
    print(' *** {:5.2f}'.format(kElapsed))
    #########################################################################
    time.sleep(random.uniform(5, 6) ) # sleep before sending nxt cmd.
    
    print('\n Main. Stopping threads.')
    for ii in range(1,numThreads+1):
        toSend = { 'cmdTo': wrkThrd2SendTo, 'cmdFrom': mainThreadIdx,
                   'cmd': 'quit', 'seqNum':seqNum }
        incSeqNum(lock)
        qDict[ii][ 'cq' ].put(toSend)
    #########################################################################

