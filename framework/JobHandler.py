'''
Created on Mar 5, 2013

@author: crisr
'''
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)

try:
  import Queue as queue
except:
  import queue
import subprocess
import os
import signal
import logging, logging.handlers
import threading

class ExternalRunner:
  def __init__(self,command,workingDir,output=None):
    ''' Initialize command variable'''
    self.command    = command

    if    output!=None: 
      self.output = output
      self.identifier =  str(output).split("~")[1]
    else: 
      self.output = os.path.join(workingDir,'generalOut')
      self.identifier = 'generalOut'
    ''' Initialize logger'''
    #self.logger     = self.createLogger(self.identifier)
    #self.addLoggerHandler(self.identifier, self.output, 100000, 1)
    
    self.__workingDir = workingDir

  '''
    Function to create a logging object
    @ In, name: name of the logging object
    @ Out, logging object 
  '''
  def createLogger(self,name):
    return logging.getLogger(name)
  '''
    Function to create a logging object
    @ In, logger_name     : name of the logging object
    @ In, filename        : log file name (with path)
    @ In, max_size        : maximum file size (bytes)
    @ In, max_number_files: maximum number of files to be created
    @ Out, None 
  '''
  def addLoggerHandler(self,logger_name,filename,max_size,max_number_files):
    hadler = logging.handlers.RotatingFileHandler(filename,'a',max_size,max_number_files)
    logging.getLogger(logger_name).addHandler(hadler)
    logging.getLogger(logger_name).setLevel(logging.INFO)
    return 

  '''
    Function that logs every line received from the out stream
    @ In, out_stream: output stream
    @ In, logger    : the instance of the logger object
    @ Out, logger   : the logger itself 
  '''
  def outStreamReader(self, out_stream):
    while True:
      line = out_stream.readline()
      if len(line) == 0 or not line:
        break
      self.logger.info('%s', line)
      #self.logger.debug('%s', line.srip())

  def isDone(self):
    self.__process.poll()
    if self.__process.returncode != None:
      return True
    else:
      return False

  def getReturnCode(self):
    return self.__process.returncode
  
  def start(self):
    oldDir = os.getcwd()
    os.chdir(self.__workingDir)
    localenv = dict(os.environ)
    localenv['PYTHONPATH'] = ''
    outFile = open(self.output,'w')
    self.__process = subprocess.Popen(self.command,shell=True,stdout=outFile,stderr=outFile,cwd=self.__workingDir,env=localenv)
    #self.__process = subprocess.Popen(self.command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=self.__workingDir,env=localenv)
    #self.thread = threading.Thread(target=self.outStreamReader, args=(self.__process.stdout,)) 
    #self.thread.daemon = True
    #self.thread.start()

    os.chdir(oldDir)
  
  def kill(self):
    #In python 2.6 this could be self.process.terminate()
           
    print("JOB HANDLER   : Terminating ",self.__process.pid,self.command)
    os.kill(self.__process.pid,signal.SIGTERM)    

  def getWorkingDir(self):
    return self.__workingDir


class JobHandler:
  def __init__(self):
    self.runInfoDict       = {}
    self.external          = True
    self.mpiCommand        = ''
    self.threadingCommand  = ''
    self.submitDict = {}
    self.submitDict['External'] = self.addExternal
    self.submitDict['Internal'] = self.addInternal
    self.externalRunning        = []
    self.internalRunning        = []
    self.__running = []
    self.__queue = queue.Queue()
    self.__nextId = 0
    self.__numSubmitted = 0
    
  def initialize(self,runInfoDict):
    self.runInfoDict = runInfoDict
    if self.runInfoDict['ParallelProcNumb'] !=1 and len(self.runInfoDict['ParallelCommand']) > 0:
      self.mpiCommand = self.runInfoDict['ParallelCommand']+' '+str(self.runInfoDict['ParallelProcNumb'])
    if self.runInfoDict['ThreadingProcessor'] !=1:
      self.threadingCommand = self.runInfoDict['ThreadingCommand'] +' '+str(self.runInfoDict['ThreadingProcessor'])
    #initialize PBS
    self.__running = [None]*self.runInfoDict['batchSize']

  def addExternal(self,executeCommand,outputFile,workingDir):
    #probably something more for the PBS
    command = self.runInfoDict['precommand']
    if self.mpiCommand !='':
      command += self.mpiCommand+' '
    if self.threadingCommand !='':
      command +=self.threadingCommand+' '
    command += executeCommand
    command += self.runInfoDict['postcommand']
    self.__queue.put(ExternalRunner(command,workingDir,outputFile))
    self.__numSubmitted += 1

  def isFinished(self):
    if not self.__queue.empty():
      return False
    for i in range(len(self.__running)):
      if self.__running[i] and not self.__running[i].isDone():
        return False
    return True

  def howManyFreeSpots(self):
    cnt_free_spots = 0
    if self.__queue.empty():
      for i in range(len(self.__running)):
        if self.__running[i]:
          if self.__running[i].isDone():
            cnt_free_spots += 1
        else:
          cnt_free_spots += 1
    return cnt_free_spots
    

  def getFinished(self, removeFinished=True):
    #print("getFinished "+str(self.__running)+" "+str(self.__queue.qsize()))
    finished = []
    for i in range(len(self.__running)):
      if self.__running[i] and self.__running[i].isDone():
        finished.append(self.__running[i])
        if removeFinished:
          running = self.__running[i]
          returncode = running.getReturnCode()
          if returncode != 0:
            print("JOB HANDLER   : Process Failed",running,running.command," returncode",returncode)
          self.__running[i] = None
    if self.__queue.empty():
      return finished
    for i in range(len(self.__running)):
      if self.__running[i] == None and not self.__queue.empty(): 
        item = self.__queue.get()          
        command = item.command
        command = command.replace("%INDEX%",str(i))
        command = command.replace("%INDEX1%",str(i+1))
        command = command.replace("%CURRENT_ID%",str(self.__nextId))
        command = command.replace("%CURRENT_ID1%",str(self.__nextId+1))
        command = command.replace("%SCRIPT_DIR%",self.runInfoDict['ScriptDir'])
        command = command.replace("%FRAMEWORK_DIR%",self.runInfoDict['FrameworkDir'])
        command = command.replace("%WORKING_DIR%",item.getWorkingDir())
        command = command.replace("%METHOD%",os.environ.get("METHOD","opt"))
        command = command.replace("%NUM_CPUS%",str(self.runInfoDict['ParallelProcNumb']))
        item.command = command
        self.__running[i] = item
        self.__running[i].start()
        self.__nextId += 1

    return finished

  def getFinishedNoPop(self):
    return self.getFinished(False)

  def getNumSubmitted(self):
    return self.__numSubmitted

  def addInternal(self):
    return
  
  def terminateAll(self):
    #clear out the queue
    while not self.__queue.empty():
      self.__queue.get()
    for i in range(len(self.__running)):
      self.__running[i].kill()


