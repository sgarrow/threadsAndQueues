import threading
import queue
import time
import random
printPad =  ' ' * 70
#############################################################################

def workerFunction( *args ):
    myThreadName = args[0]
    x  = random.uniform( .01, 1.0 )
    time.sleep( x )
    #print(' {} {}. Wrk: {:5.2f} sec.'.format(printPad,myThreadName,x))
    return x
#############################################################################

def aThreadWhileOneLoop( *args ):
    myThrNum     = args[0]
    qDict        = args[1]
    myCommandQ   = qDict[myThrNum]['cq']
    myThreadName = threading.current_thread().name
     
    while(1):

        x  = random.uniform( .01, 1.0 )
        time.sleep( x )

        try:                          # Look for a command. 
            command = myCommandQ.get( block = False )
        except queue.Empty:
            continue

        print(' {} {}. Get: {}.'.format(printPad, myThreadName, command), flush = True)
        if command['cmd'] == 'quit':  # Terminate command received?
            break
        elif command['cmd'] == 'wrk': # Some other command received?

            workerRsp = '{:4.2f}'.format(workerFunction(myThreadName)) # If so, spend time doing work.

            toSend = { 'rspTo': command['cmdFrom'], 'rspFrom': myThrNum, 'rsp': workerRsp, 'seqNum': command['seqNum'] }

            print( ' {} {}. Put: {}.'.format(printPad,myThreadName, toSend), flush = True)

            myRespondToQ = qDict[command['cmdFrom']]['rq']
            myRespondToQ.put( toSend )

    return 0
#############################################################################

def mainThread0( *args ):
    return 0
#############################################################################

if __name__ == '__main__':

    qDict         = {} # A place to hold all Q's for all threads (and main).
    tLst          = [] # List of functions to be passed to 'create thread'.
    numThreads    = 5  # N+1 when counting the 'main' thread.
    mainThreadIdx = 0  # Threads numbered 1,2,... and 0 is reserved for main.

    # Create a list of functions. The first one is just kind of a Dummy to
    # make sure that the 'main' thread as well as all the 'worker' threads,
    # get queues (command, response, message) allocated for it.
    threadFunctionLst = [mainThread0] + numThreads * [aThreadWhileOneLoop]

    # Create a dictionary. The keys are integers 0 to len(threadFunctionLst)-1.
    # The values are a sub-dictionary of two Qs, command, response.
    # For example:
    # qDict[1][cq]: Where Thrd1 looks for cmds sent to it by other thrds (or main).
    # qDict[1][rq]: Where Thrd1 looks for responses to cmds it sent to other thrds.
    #               Note: Commands generate Responses ... Messages don't.
    print('\n Main. Creating Queues.')
    for t in range( len( threadFunctionLst ) ):
        qDict[t] = { 'cq': queue.Queue(),
                     'rq': queue.Queue()}

    # Create all the threads.
    print(' Main. Creating worker threads.' )
    for t in range( 1,len( threadFunctionLst ) ): # <-- 1 causes Dummy to be skipped.
        tLst.append( threading.Thread( group  = None, 
                                       target = threadFunctionLst[t], 
                                       name   = 'Thr{}'.format(t),

                                       # t = thread number. A given thread uses
                                       # this parameter to know its index into 
                                       # the Q Dict ... the 2nd parameter.
                                       args = ( t, qDict ), 

                                       kwargs = {}, 
                                       daemon = None ) )

    # Start all the threads.
    print(' Main. Starting worker threads.')
    for t in tLst:
        t.start()

    # Send commands to the threads.  Keep track of how many 
    # cmds are sent to know how many responses to expect.
    print(' Main: Sending cmds to Threads.\n')
    numCmdsToSend = 10
    numRspRcvd    = 0
    seqNum = 0
    for ii in range(numCmdsToSend):

        # Send a cmd to a random thread.
        wrkThrd2SendTo = random.randint( 1, len( tLst ) )
        toSend = { 'cmdTo': wrkThrd2SendTo, 'cmdFrom': mainThreadIdx, 'cmd': 'wrk', 'seqNum':seqNum }
        seqNum += 1
        print(' Main. Put: {}.'.format(toSend), flush = True)
        qDict[ wrkThrd2SendTo ]['cq'].put( toSend )

        # Check for any responses.
        try:
            cmdRsp = qDict[mainThreadIdx]['rq'].get(block = False)
        except queue.Empty:
            cmdRsp = None
        else:
            print(' Main. Get: {}.'.format(cmdRsp), flush = True)
            numRspRcvd += 1

        # sleep a bit before sending the next cmd.
        x = random.uniform( .01, 1.0 )
        time.sleep( x )

    # Wait for all the threads to send all their responses.
    print(' Main: Waiting for all responses.')
    while numRspRcvd < numCmdsToSend:
        try:
            cmdRsp = qDict[mainThreadIdx]['rq'].get( block = False )       
        except queue.Empty:
            cmdRsp = None
        else:
            print(' Main. Get: {}.'.format(cmdRsp), flush = True)
            numRspRcvd += 1

    # Kill all the threads because I hate them.
    print( '\n Main. Killing all worker threads.' )
    for t in range( 1,len( threadFunctionLst ) ):
        toSend = { 'cmdTo': wrkThrd2SendTo, 'cmdFrom': mainThreadIdx, 'cmd': 'quit', 'seqNum':seqNum }
        seqNum += 1
        qDict[ t ][ 'cq' ].put( toSend )
#############################################################################

