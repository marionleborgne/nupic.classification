from model_params.template_model_params import MODEL_PARAMS as TEMPLATE_MODEL_PARAMS
import csv
import os

from settings import SIGNAL_TYPES, MODEL_PARAMS_DIR, DATA_DIR


class IncorrectHeadersException(Exception):
  pass

def create_model_params(model_param_dir, model_param_name, file_name):
  
  # get the scalar values
  values = []
  with open(file_name, 'rU') as inputFile:
    csvReader = csv.reader(inputFile)
    headers = csvReader.next()
    
    # skip the rest of the header rows
    csvReader.next()
    csvReader.next()
    
    if headers[0] != 'x':
      raise IncorrectHeadersException("first column should be named 'x' but is '%s'" %headers[0])
    if headers[1] != 'y':
      raise IncorrectHeadersException("first column should be named 'y' but is '%s'" %headers[1])
  
    for line in csvReader:
      values.append(float(line[1]))
      
  # make sure the directory exists
  if not os.path.exists(model_param_dir):
      os.makedirs(model_param_dir)
      
  # make sure there is an init file so that we can import the model_params file later 
  with open("%s/%s" % (model_param_dir, "__init__.py"), 'wb') as initFile:
    initFile.write("")
    
  # write the new model_params file
  with open("%s/%s.py" % (model_param_dir, model_param_name), 'wb') as modelParamsFile:
    min_value = min(values)
    max_value = max(values)
    mp = TEMPLATE_MODEL_PARAMS
    mp['modelParams']['sensorParams']['encoders']['y']['maxval'] = max_value
    mp['modelParams']['sensorParams']['encoders']['y']['minval'] = min_value
    modelParamsFile.write("MODEL_PARAMS = %s" % repr(mp))



if __name__ == "__main__":
  
  for signal_type in SIGNAL_TYPES:
    file_name = '%s/%s.csv' % (DATA_DIR, signal_type)
    model_params_name = '%s_model_params' % signal_type
    create_model_params(MODEL_PARAMS_DIR, model_params_name, file_name)