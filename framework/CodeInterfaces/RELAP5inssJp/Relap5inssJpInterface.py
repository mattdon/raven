"""
Created on July 20, 2016

@author: alfoa

This is a code interface for the modified version of RELAP5 mantained by the INSS Japan
"""
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)

import os
import copy
import relapdata
import re
import shutil
from Relap5Interface import Relap5
from GenericParser import GenericParser

class Relap5inssJp(Relap5):
  """
    this class is used a part of a code dictionary to specialize Model.Code for RELAP5-3D Version 4.0.3
  """
  def createNewInput(self,currentInputFiles,oriInputFiles,samplerType,**Kwargs):
    """
      this generate a new input file depending on which sampler is chosen
      @ In, currentInputFiles, list,  list of current input files (input files from last this method call)
      @ In, oriInputFiles, list, list of the original input files
      @ In, samplerType, string, Sampler type (e.g. MonteCarlo, Adaptive, etc. see manual Samplers section)
      @ In, Kwargs, dictionary, kwarded dictionary of parameters. In this dictionary there is another dictionary called "SampledVars"
             where RAVEN stores the variables that got sampled (e.g. Kwargs['SampledVars'] => {'var1':10,'var2':40})
      @ Out, newInputFiles, list, list of newer input files, list of the new input files (modified and not)
    """
    import RELAPparser
    found = False
    foundModelPar = False
    modelParIndex = 0
    for indexInputDeck, inputFile in enumerate(currentInputFiles):
      if inputFile.getExt() in self.getInputExtension() and inputFile.getBase() not in 'modelpar.inp':
        found = True
        break
    for indexModelPar, inputFile in enumerate(currentInputFiles):
      if inputFile.getBase() in 'modelpar.inp':
        foundModelPar = True
        modelParIndex = indexModelPar
        break
    if not foundModelPar: raise IOError('Additional input file modelpar.inp not provided!!!!!!! ')
    if not found        : raise IOError('None of the input files has one of the following extensions: ' + ' '.join(self.getInputExtension()))
    parser = RELAPparser.RELAPparser(currentInputFiles[indexInputDeck].getAbsFile())
    modifDict = self.pointSamplerForRELAP5(**Kwargs) if not samplerType.endswith('EventTree') else self.DynamicEventTreeForRELAP5(**Kwargs)
    parser.modifyOrAdd(modifDict,True)
    parser.printInput(currentInputFiles[indexInputDeck])
    # check and modify modelpar.inp file
    modelparParser = GenericParser([currentInputFiles[modelParIndex]])
    modelparParser.modifyInternalDictionary(**Kwargs)
    modelparParser.writeNewInput([currentInputFiles[modelParIndex]],[oriInputFiles[modelParIndex]])
    return currentInputFiles



