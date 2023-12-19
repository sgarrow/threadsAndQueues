import threading
import queue
import time
import random
#############################################################################

def workerFunction( *args ):
    x  = random.uniform( .1, 3.0 )
    time.sleep( x )
    return 0
#############################################################################

def workerThread( *args ):
    myThreadNumber = args[0]
    myCommandQ     = args[1][myThreadNumber]['cq']
    myMessageQ     = args[1][myThreadNumber]['mq']
     
    while(1):

        try:                            # Look for a message.
            message = myMessageQ.get( block = True, timeout = .1 )
        except queue.Empty:
            message = ''
        else:
            print(' Thread-{}. Getting: {}.'.format(myThreadNumber, message))

        try:                            # Look for a command. 
            command = myCommandQ.get( block = True, timeout = .1 )
        except queue.Empty:
            command = ''
        else:
            print( ' Thread-{}. Getting: {}.'.format(myThreadNumber,command))

        if command == 'q':              # Terminate command received?
            break
        elif command != '':             # Some other command received?
            response = workerFunction() # If so, spend time doing work.
            myRespondToQ = args[1][command[2]]['rq']
            myRespondToQ.put( ' Thread-{}. Rsp To cmd {}.'.\
                format(myThreadNumber, command[3]) )
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
    threadFunctionLst = [mainThread0] +numThreads*[workerThread]

    # Create a dictionary. The keys are integers 0 to len(threadFunctionLst)-1.
    # The values are a sub-dictionary of three Qs, command, response, message.
    # For example:
    # qDict[1][cq]: Where Thrd1 looks for cmds sent to it by other thrds (or main).
    # qDict[1][rq]: Where Thrd1 looks for responses to cmds it sent to other thrds.
    # qDict[1][mq]: Where Thrd1 looks for msgs sent to it by other thrds (or main).
    #               Note: Commands generate Responses ... Messages don't.
    print('\n     Main. Creating Queues.')
    for t in range( len( threadFunctionLst ) ):
        qDict[t] = { 'cq': queue.Queue(),
                     'rq': queue.Queue(),
                     'mq': queue.Queue() }

    # Create all the threads.
    print('     Main. Creating worker threads.' )
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
    print('     Main. Starting worker threads.\n')
    for t in tLst:
        t.start()

    # Send commands/messages to the threads.  Keep track of how many 
    # cmds are sent to know how many responses to expect.
    print(' Main: Sending cmds/msgs (random) to 1 of 3 Threads (random).')
    numResponsesExpected = 0
    for ii in range(20):

        cmdOrMsg       = 'cq' if random.randint( 0, 1 ) else 'mq'
        wrkThrd2SendTo = random.randint( 1, len( tLst ) )
        sendResponseTo = mainThreadIdx
        # Note the message format.  Threads know this apriori.
        toSend         = [ cmdOrMsg, wrkThrd2SendTo, sendResponseTo, ii ]
        print( '     Main. Putting: {}.'.format(toSend))
        qDict[ wrkThrd2SendTo ][ cmdOrMsg ].put( toSend )

        x = random.uniform( .1, .3 )
        time.sleep( x )

        if cmdOrMsg == 'cq':
            numResponsesExpected += 1

    # Wait for all the threads to send all their responses.
    while qDict[0]['rq'].qsize() < numResponsesExpected:
        print('     Main. Expected/Received Responses = {}/{}.'.\
            format(numResponsesExpected, qDict[0]['rq'].qsize() ))
        time.sleep(.5)
    print('     Main. Expected/Received Responses = {}/{}.'.\
        format(numResponsesExpected, qDict[0]['rq'].qsize() ))

    # Kill all the threads because I hate them.
    print( '\n     Main. Killing all worker threads.' )
    for t in range( 1,len( threadFunctionLst ) ):
        qDict[ t ][ 'cq' ].put( 'q' )

    print( '\n     Main. Printing all collected responses.' )
    for ii in range(numResponsesExpected):
        response = qDict[0]['rq'].get( block = True, timeout = .2 )
        print(response)
#############################################################################

