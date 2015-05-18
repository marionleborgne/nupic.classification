#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
A simple example showing how to use classification for detecting known
anomalies even if they occur again. There are two different methods shown here.
"""

import csv
import importlib
import pprint

from nupic.data.datasethelpers import findDataset
from nupic.frameworks.opf.modelfactory import ModelFactory

from settings import ANOMALY_RANGES, RESULTS_DIR, SIGNAL_TYPES


def createModel(metricName):
  model_params = getModelParamsFromName(metricName)
  return ModelFactory.create(model_params)


def trainAndClassify(model, data_path, results_path):
  """
  In this function we explicitly label specific portions of the data stream.
  Any later record that matches the pattern will get labeled the same way.
  """

  model.enableInference({'predictedField': 'y'})

  # Here we will get the classifier instance so we can add and query labels.
  classifierRegion = model._getAnomalyClassifier()
  classifierRegionPy = classifierRegion.getSelf()

  # We need to set this classification type. It is supposed to be the default
  # but is not for some reason.
  classifierRegionPy.classificationVectorType = 2

  with open (findDataset(data_path)) as fin:
    reader = csv.reader(fin)
    headers = reader.next()
    csvWriter = csv.writer(open(results_path,"wb"))
    csvWriter.writerow(["x", "y", "label", "anomalyScore", "anomalyLabel"])
    for x, record in enumerate(reader):
      modelInput = dict(zip(headers, record))
      label = int(modelInput['label'])
      modelInput["y"] = float(modelInput["y"])
      result = model.run(modelInput)
      anomalyScore = result.inferences['anomalyScore']
      anomalyLabel = result.inferences['anomalyLabel']


      # Manually tell the classifier to learn the first few artificial
      # anomalies. From there it should catch many of the following
      # anomalies, even though the anomaly sore might be low.
      
      for anomaly_range in ANOMALY_RANGES:
        start = anomaly_range['start']
        end = anomaly_range['end']
        label = "label1"

        if x>= start and x<=end:
          anomalyLabel = "['%s']" %label
      
        if x == end + 2:
          print "Adding labeled anomalies for record",x
          classifierRegion.executeCommand(["addLabel",str(start),str(end+1),label])

      csvWriter.writerow([x, modelInput["y"], label, anomalyScore, anomalyLabel])

  #print "Anomaly scores have been written to %s" % _RESULTS_PATH
  #print "The following labels were stored in the classifier:"
  #labels = eval(classifierRegion.executeCommand(["getLabels"]))
  #pprint.pprint(labels)


def computeClassificationAccuracy(result_file):
  false_positive = 0
  false_negative = 0
  
  with open (findDataset(result_file)) as fin:
    reader = csv.reader(fin)
    headers = reader.next()
    for i, record in enumerate(reader):
      data = dict(zip(headers, record))
      
      if data['anomalyLabel'] == "['label1']" and data['label'] != "1":
          false_positive +=1
          #print "False positive: %s, %s, %s" % (i, data['anomaly'], data['anomalyLabel']) 
      if data['anomalyLabel'] == "[]" and data['label'] != "0":
          false_negative +=1 
          #print "False negative: %s, %s, %s" % (i, data['anomaly'], data['anomalyLabel']) 
          
          
  print ""
  print "== Classification accuracy for %s ==" % results_path
  print "* False positive: %s" % false_positive
  print "* False negative: %s" % false_negative
  print ""


def getModelParamsFromName(metricName):
  
  importName = "model_params.%s_model_params" % metricName
    
  print "Importing model params from %s" % importName
  try:
    importedModelParams = importlib.import_module(importName).MODEL_PARAMS
  except ImportError:
    raise Exception("No model params exist for '%s'" % importName)
  return importedModelParams

if __name__ == "__main__":
  
  for signal_type in SIGNAL_TYPES: 
    data_path = "%s.csv" % signal_type
    results_path = "%s/%s.csv" % (RESULTS_DIR, signal_type)
    
    model = createModel(signal_type)
    trainAndClassify(model, data_path, results_path)
    computeClassificationAccuracy(results_path)
