import threading
import queue
import time
import random
pad =  ' ' * 70
#############################################################################

def workFunc1(*args):
    myThrNme = args[0]
    x  = random.uniform(.01, 9.0)
    time.sleep(x)
    #print(' {} {}. Wrk: {:5.2f} sec.'.format(pad,myThrNme,x))
    return x
#############################################################################

def aThreadWhileOneLoop(*args):
    myThrNum   = args[0]
    qDict      = args[1]
    myCommandQ = qDict[myThrNum]['cq']
    myThrNme   = threading.current_thread().name
     
    while(1):
        x  = random.uniform(.01, 1.0)
        time.sleep(x)

        try:                      # Look for a command. 
            cmd = myCommandQ.get(block = False)
        except queue.Empty:
            continue

        print(' {} {}. Get: {}.'.format(pad, myThrNme, cmd), flush = True)
        if cmd['cmd'] == 'quit':  # Terminate command received?
            break
        elif cmd['cmd'] == 'wrk': # Some other command received?
                                  # If so, spend time doing work. 
            wrkRsp = '{:4.2f}'.format(workFunc1(myThrNme)) 

            toSend = { 'rspTo': cmd['cmdFrom'], 'rspFrom': myThrNum, 
                       'rsp':   wrkRsp, 'seqNum': cmd['seqNum'] }

            print(' {} {}. Put: {}.'.format(pad,myThrNme,toSend),flush=True)

            myRespondToQ = qDict[cmd['cmdFrom']]['rq']
            myRespondToQ.put(toSend)
    return 0
#############################################################################

def mainThread0(*args):
    return 0
#############################################################################

if __name__ == '__main__':

    qDict         = {} # A place to hold all Q's for all threads (and main).
    tLst          = [] # List of functions to be passed to 'create thread'.
    numThreads    = 7  # N+1 when counting the 'main' thread.
    mainThreadIdx = 0  # Threads numbered 1,2,... and 0 is reserved for main.

    # Create a list of funcs. The first one is a Dummy to  make sure that the
    # 'main' thread as well as all the 'worker' threads, get Qs allocated.
    threadFunctionLst = [mainThread0] + numThreads * [aThreadWhileOneLoop]

    # Create a dictionary. The keys are integers 0 to len(threadFunctLst)-1.
    # The values are a sub-dictionary of two Qs, command, response.
    # e.g. qDict[1][cq]: Where Thrd1 looks for cmds sent to it.
    #      qDict[1][rq]: Where Thrd1 looks for responses to cmds it.
    print('\n Main. Creating Queues.')
    for t in range(len(threadFunctionLst)):
        qDict[t] = {'cq': queue.Queue(), 'rq': queue.Queue()}

    # Create all the threads.
    print(' Main. Creating worker threads.')
    for t in range(1,len(threadFunctionLst)): # <- 1 RE: skip Dummy.
        tLst.append(threading.Thread(group  = None, 
                                     target = threadFunctionLst[t], 
                                     name   = 'Thr{}'.format(t),
                                     # Threads use t as its idx into qDict.
                                     args = (t, qDict),
                                     kwargs = {}, 
                                     daemon = None))

    # Start the threads.
    print(' Main. Starting worker threads.')
    for t in tLst:
        t.start()

    # Send commands to the threads.  Keep track of how many 
    # cmds are sent to know how many responses to expect.
    print(' Main: Sending cmds to Threads.\n')
    numCmdsToSend = 50
    numRspRcvd    = 0
    seqNum        = 0
    for ii in range(numCmdsToSend):

        # Send a cmd to a random thread.
        wrkThrd2SendTo = random.randint(1, len(tLst))
        toSend = { 'cmdTo': wrkThrd2SendTo, 'cmdFrom': mainThreadIdx, 
                   'cmd': 'wrk', 'seqNum':seqNum }
        seqNum += 1
        print(' Main. Put: {}.'.format(toSend), flush = True)
        qDict[ wrkThrd2SendTo ]['cq'].put(toSend)

        # Check for any responses.
        try:
            cmdRsp = qDict[mainThreadIdx]['rq'].get(block = False)
        except queue.Empty:
            cmdRsp = None
        else:
            print(' Main. Get: {}.'.format(cmdRsp), flush = True)
            numRspRcvd += 1
        
        time.sleep(random.uniform(.01, 1.0) ) # sleep before sending nxt cmd.

    # Wait for all the threads to send all their responses.
    print('\n Main: Waiting for all responses.')
    while numRspRcvd < numCmdsToSend:
        try:
            cmdRsp = qDict[mainThreadIdx]['rq'].get(block = False)       
        except queue.Empty:
            continue
        else:
            print(' Main. Get: {}.'.format(cmdRsp), flush = True)
            numRspRcvd += 1

    # Kill all the threads.
    print('\n Main. Killing all worker threads.')
    for t in range(1,len( threadFunctionLst)):
        toSend = { 'cmdTo': wrkThrd2SendTo, 'cmdFrom': mainThreadIdx,
                   'cmd': 'quit', 'seqNum':seqNum }
        seqNum += 1
        qDict[ t ][ 'cq' ].put(toSend)
#############################################################################

