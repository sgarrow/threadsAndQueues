import threading
import queue
import time
import random
printPad =  ' ' * 30
#############################################################################

def workerFunction( *args ):
    myThreadNumber = args[0]
    x  = random.uniform( .1, 1.0 )
    time.sleep( x )
    print(' {} Thr{}. Wrk: {:5.2f} sec.'.format(printPad,myThreadNumber,x))
    return 0
#############################################################################

def aThreadWhileOneLoop( *args ):
    myThreadNumber = args[0]
    myCommandQ     = args[1][myThreadNumber]['cq']
     
    while(1):

        try:                            # Look for a command. 
            command = myCommandQ.get( block = False, timeout = .1 )
        except queue.Empty:
            command = ''
        else:
            print(' {} Thr{}. Get: {}.'.format(printPad, myThreadNumber,command), flush = True)

        if command == 'q':              # Terminate command received?
            break
        elif command != '':             # Some other command received?
            response = workerFunction(myThreadNumber) # If so, spend time doing work.

            #myStr = ' Thread-{}. Putting: {}.'.format(myThreadNumber, message)
            #print('{:>81}'.format(myStr), flush = True)

            myRespondToQ = args[1][command[1]]['rq']
            myRespondToQ.put( ' Thr{}. put rsp to cmd {}.'.\
                format(myThreadNumber, command[2]) )
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
                                       name   = None,

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
    for ii in range(numCmdsToSend):

        # Send a cmd to a random thread.
        wrkThrd2SendTo = random.randint( 1, len( tLst ) )
        sendResponseTo = mainThreadIdx
        toSend         = [ wrkThrd2SendTo, sendResponseTo, ii ]
        print(' Main. Put Cmd: {}.'.format(toSend), flush = True)
        qDict[ wrkThrd2SendTo ]['cq'].put( toSend )

        # sleep a bit before sending the next cmd.
        x = random.uniform( .01, .1 )
        time.sleep( x )

    # Wait for all the threads to send all their responses.
    while qDict[0]['rq'].qsize() < numCmdsToSend:
        print(' Main. Exp/Rcvd Resps = {}/{}.'.format(numCmdsToSend, qDict[0]['rq'].qsize()), flush = True)
    print(' Main. Exp/Rcvd Rsps = {}/{}.'.format(numCmdsToSend, qDict[0]['rq'].qsize()), flush = True)

    # Kill all the threads because I hate them.
    print( '\n Main. Killing all worker threads.' )
    for t in range( 1,len( threadFunctionLst ) ):
        qDict[ t ][ 'cq' ].put( 'q' )

    print( '\n Main. Printing all collected responses.' )
    for ii in range(numCmdsToSend):
        response = qDict[0]['rq'].get( block = True, timeout = .2 )
        print(response)
#############################################################################

