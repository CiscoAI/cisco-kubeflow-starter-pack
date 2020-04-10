import tensorflow as tf
import pandas as pd
import numpy as np
import shutil
import os
from sklearn.preprocessing import OneHotEncoder

BLE_RSSI = pd.read_csv('/opt/iBeacon_RSSI_Labeled.csv') #Labeled dataset

# Configure model options
TF_DATA_DIR = os.getenv("TF_DATA_DIR", "/tmp/data/")
TF_MODEL_DIR = os.getenv("TF_MODEL_DIR", None)
TF_EXPORT_DIR = os.getenv("TF_EXPORT_DIR", "rssi/")
TF_MODEL_TYPE = os.getenv("TF_MODEL_TYPE", "DNN")
TF_TRAIN_STEPS = int(os.getenv("TF_TRAIN_STEPS", 1))
TF_BATCH_SIZE = int(os.getenv("TF_BATCH_SIZE", 32))
TF_LEARNING_RATE = float(os.getenv("TF_LEARNING_RATE", 0.01))


# Feature columns
COLUMNS = list(BLE_RSSI.columns)
FEATURES = COLUMNS[2:]
LABEL = [COLUMNS[0]]

def make_feature_cols():
    input_columns = [tf.feature_column.numeric_column(k) for k in FEATURES]
    return input_columns

def main(unused_args):

  tf.logging.set_verbosity(tf.logging.INFO)

  df_full = pd.read_csv('/opt/iBeacon_RSSI_Labeled.csv') #Labeled dataset

  # Input Data Preprocessing
  df_full = df_full.drop(['date'],axis = 1)
  df_full[FEATURES] = (df_full[FEATURES]-df_full[FEATURES].mean())/df_full[FEATURES].std()

  #Output Data Preprocessing

  dict = {'O02': 0,'P01': 1,'P02': 2,'R01': 3,'R02': 4,'S01': 5,'S02': 6,'T01': 7,'U02': 8,'U01': 9,'J03': 10,'K03': 11,'L03': 12,'M03': 13,'N03': 14,'O03': 15,'P03': 16,'Q03': 17,'R03': 18,'S03': 19,'T03': 20,'U03': 21,'U04': 22,'T04': 23,'S04': 24,'R04': 25,'Q04': 26,'P04': 27,'O04': 28,'N04': 29,'M04': 30,'L04': 31,'K04': 32,'J04': 33,'I04': 34,'I05': 35,'J05': 36,'K05': 37,'L05': 38,'M05': 39,'N05': 40,'O05': 41,'P05': 42,'Q05': 43,'R05': 44,'S05': 45,'T05': 46,'U05': 47,'S06': 48,'R06': 49,'Q06': 50,'P06': 51,'O06': 52,'N06': 53,'M06': 54,'L06': 55,'K06': 56,'J06': 57,'I06': 58,'F08': 59,'J02': 60,'J07': 61,'I07': 62,'I10': 63,'J10': 64,'D15': 65,'E15': 66,'G15': 67,'J15': 68,'L15': 69,'R15': 70,'T15': 71,'W15': 72,'I08': 73,'I03': 74,'J08': 75,'I01': 76,'I02': 77,'J01': 78,'K01': 79,'K02': 80,'L01': 81,'L02': 82,'M01': 83,'M02': 84,'N01': 85,'N02': 86,'O01': 87,'I09': 88,'D14': 89,'D13': 90,'K07': 91,'K08': 92,'N15': 93,'P15': 94,'I15': 95,'S15': 96,'U15': 97,'V15': 98,'S07': 99,'S08': 100,'L09': 101,'L08': 102,'Q02': 103,'Q01': 104}
  df_full['location'] = df_full['location'].map(dict)
  df_train=df_full.sample(frac=0.8,random_state=200)
  df_valid=df_full.drop(df_train.index)

  location_counts = BLE_RSSI.location.value_counts()

  # Train Input Function
  train_input_fn = tf.estimator.inputs.pandas_input_fn(
    x = df_train[FEATURES],
    y = df_train['location'],
    batch_size = 32,
    num_epochs = 10,
    shuffle = False,
    queue_capacity = 10,
    num_threads = 1
  )

  # Test Input Function
  test_input_fn = tf.estimator.inputs.pandas_input_fn(
    x = df_train[FEATURES],
    y = df_train['location'],
    batch_size = 32,
    num_epochs = 10,
    shuffle = True,
    queue_capacity = 10,
    num_threads = 1
  )

  feature_columns =  make_feature_cols()
  feature_spec = tf.feature_column.make_parse_example_spec(feature_columns)

  #Serving Input Reciever Function for model export

  serving_input_receiver_fn = tf.estimator.export.build_parsing_serving_input_receiver_fn(feature_spec)

  TF_MODEL_DIR1 = '/mnt/'
  config = tf.estimator.RunConfig(model_dir=TF_MODEL_DIR1, save_summary_steps=10, save_checkpoints_steps=10)
  
  # Build 3 layer DNN classifier

  model = tf.estimator.DNNClassifier(hidden_units = [13,65,110],
                     feature_columns = feature_columns,
                     model_dir = TF_MODEL_DIR,
                     n_classes=105, config=config
                   )
  TF_EXPORT_DIR1='/mnt/'
  export_final = tf.estimator.FinalExporter(TF_EXPORT_DIR1, serving_input_receiver_fn=serving_input_receiver_fn)

  train_spec = tf.estimator.TrainSpec(input_fn=train_input_fn,
                                        max_steps=TF_TRAIN_STEPS)

  eval_spec = tf.estimator.EvalSpec(input_fn=test_input_fn,
                                      steps=1,
                                      exporters=export_final,
                                      throttle_secs=1,
                                      start_delay_secs=1)

  # Train and Evaluate the model

  tf.estimator.train_and_evaluate(model, train_spec, eval_spec)
  output_dir = "/mnt/"
  export_dir = model.export_savedmodel(output_dir, serving_input_receiver_fn)

if __name__ == "__main__":
    tf.app.run()
