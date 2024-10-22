# -*- coding: utf-8 -*-
"""natural gas spot price.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/10XBY8381YUkmfUxWPQ39W58UvFHOKRkl
"""

import pandas as pd
import pywt
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm  
from datetime import datetime
import math
import scipy as sp
import sklearn
!pip install xlrd
from google.colab import files
from sklearn.preprocessing import MinMaxScaler
!pip install missingno
import missingno as msno
plt.style.use('dark_background')
from sklearn import metrics # for the check the error and accuracy of the model
from sklearn.metrics import mean_squared_error,r2_score

uploaded = files.upload()

df = pd.read_excel("Natural_Gas_Spot_Price .xlsx", parse_dates = True, index_col=0)
df.head()

# Rename columns 
df= df.rename(
    columns={
        "Henry Hub Natural Gas Spot Price Dollars per Million Btu": "gas price",
        #"Day": "date"
    }
)
df.head()

#df = df.set_index('Day')
df = df.sort_index(ascending=True)
df.head()

df.isnull().sum()

df = df.fillna(method ='pad') # filling the missing values with previous ones 
df.isnull().sum()

df.head()

df.index

df.plot(figsize=(10, 5))
plt.title('Daily Natural Gas Spot Prices', fontsize=12)
plt.ylabel('Dollars per Million Btu', fontsize=12)
plt.show()

df.describe()

df.info()

"""### Splitting Data into a Training set and a Test set"""

train_data = df['1997-01-07':'2018-12-31']
test_data  = df['2019-01-01':]
print('Observations: %d' % (len(df)))
print('Train Dataset:',train_data.shape)
print('Test Dataset:', test_data.shape)

train_data.isnull().sum()

plt.figure(figsize=(10, 6))
ax = train_data.plot(figsize=(10, 6))
test_data.plot(ax=ax, color='r')
plt.legend(['train', 'test']);

"""### Normalizing the Data"""

scaler = MinMaxScaler(feature_range = (0,1))
train_data_scaled = scaler.fit_transform(train_data)
print(train_data_scaled); print(train_data_scaled.shape)

# creating a data structure with 60 time steps and 1 output.
X_train = []
y_train = []

for i in range(60, len(train_data_scaled)):
  X_train.append(train_data_scaled[i-60:i,0])
  y_train.append(train_data_scaled[i,0])
  
X_train, y_train = np.array(X_train), np.array(y_train)
print(X_train); print(); print(y_train)

print(X_train.shape)

# reshaping
# 3D tensor with shape (batch_size, timesteps, input_dim).
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
print(X_train.shape); print(); print(X_train)

from __future__ import absolute_import, division, print_function, unicode_literals

try:
  import tensorflow.compat.v2 as tf
except Exception:
  pass

tf.enable_v2_behavior()

print(tf.__version__)

!tf_upgrade_v2 -h

from tensorflow.keras import layers
from tensorflow.keras.layers import Dense, Dropout, LSTM
from tensorflow.keras.callbacks import EarlyStopping

#Build the model

# initializing RNN
model = tf.keras.Sequential()

# adding 1st LSTM layer and some dropout regularization
model.add(tf.keras.layers.LSTM(units=50, input_shape=(X_train.shape[1], 1), return_sequences=True, activation = 'relu'))
model.add(tf.keras.layers.Dropout(0.2))

# adding 2nd LSTM layer and some dropout regularization
model.add(tf.keras.layers.LSTM(units=50, return_sequences=True))
model.add(tf.keras.layers.Dropout(0.2))

# adding 3rd LSTM layer and some dropout regularization
model.add(tf.keras.layers.LSTM(units=50, return_sequences=True))
model.add(tf.keras.layers.Dropout(0.2))

# adding 4th LSTM layer and some dropout regularization
model.add(tf.keras.layers.LSTM(units=50))
model.add(tf.keras.layers.Dropout(0.2))

# adding output layer
model.add(tf.keras.layers.Dense(units=1))

#compiling RNN
model.compile(loss='mean_squared_error', optimizer='adam')

early_stopping = EarlyStopping(monitor='loss', patience=10)

# fitting RNN on training set
model.fit(X_train, y_train, epochs= 100, batch_size=32, verbose=2, callbacks=[early_stopping])

dataset_total = pd.concat((train_data, test_data), axis=0)
print(dataset_total)

print(test_data.shape)

# getting the predited natuaral gas price of 2019
# we need to append previous 60 records from training set to test set

dataset_total = pd.concat((train_data, test_data), axis=0)

inputs = dataset_total[len(dataset_total) - len(test_data)- 60:].values
inputs = inputs.reshape(-1,1)
inputs = scaler.transform(inputs) # transforming input data

X_test = []
y_test = []

for i in range (60, 262):
  X_test.append(inputs[i-60:i, 0])
  y_test.append(train_data_scaled[i,0])
  
X_test, y_test = np.array(X_test), np.array(y_test)
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
pred_price = model.predict(X_test)
pred_price = scaler.inverse_transform(pred_price)
print(pred_price)

a = pd.DataFrame(pred_price)
a.rename(columns = {0: 'Predicted'}, inplace=True); 
a.index = test_data.index
compare = pd.concat([test_data, a],1)
compare

plt.figure(figsize= (15,5))
plt.plot(compare['gas price'], color = 'red', label ="Actual Natural Gas Price")
plt.plot(compare.Predicted, color='blue', label = 'Predicted Price')
plt.title("Natural Gas Price Prediction")
plt.xlabel('Time')
plt.ylabel('Natural gas price')
plt.legend(loc='best')
plt.show()

test_score = math.sqrt(mean_squared_error(compare['gas price'], compare.Predicted))
print('Test Score: %.2f RMSE' % (test_score))

"""## Classification use-case"""

k = df.copy()

lags = 5
# Create the shifted lag series of prior trading period close values
for i in range(0, lags):
    k["Lag%s" % str(i+1)] = k["gas price"].shift(i+1).pct_change()

k['price_diff'] = k['gas price'].diff()
k['ret'] = k['gas price'].pct_change()
k.head()

# positive value = 1, otherwise, 0
k["target"] = np.where(k['price_diff']> 0, 1.0, 0.0)
k.head()

import seaborn as sns
sns.countplot(x = 'target', data=k, hue='target')
plt.show()

import math
import numpy as np
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor
import xgboost as xgb
from sklearn.metrics import accuracy_score

x = k[['Lag1', 'Lag2', 'ret']].dropna()
y = k.target.dropna()

pip install tscv

from tscv import GapKFold

# # Create training and test sets
gkcv = GapKFold(n_splits=5, gap_before=2, gap_after=1)

"""
Introduced gaps between the training and test set to mitigate the temporal dependence.
Here the split function splits the data into Kfolds. 
The test sets are untouched, while the training sets get the gaps removed
"""

for tr_index, te_index in gkcv.split(x, y):
    xTrain, xTest = x.values[tr_index], x.values[te_index];
    yTrain, yTest = y.values[tr_index], y.values[te_index];
        
print('Observations: %d' % (len(xTrain) + len(xTest)))
print('Training Observations: %d' % (len(xTrain)))
print('Testing Observations: %d' % (len(xTest)))

from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.svm import SVC, LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

# Create the (parametrised) models
print("Hit Rates/Confusion Matrices:\n")
models = [("LR", LogisticRegression()),
          ("LDA", LinearDiscriminantAnalysis()),
          ("QDA", QuadraticDiscriminantAnalysis()),
          ("LSVC", LinearSVC()),
          ("RSVM", SVC(C=1000000.0, cache_size=200, class_weight=None,
                       coef0=0.0, degree=3, gamma=0.0001, kernel='rbf',
                       max_iter=-1, probability=False, random_state=None,
                       shrinking=True, tol=0.001, verbose=False)),
          ("RF", RandomForestClassifier(
              n_estimators=1000, criterion='gini',
              max_depth=None, min_samples_split=2,
              min_samples_leaf=1, max_features='auto',
              bootstrap=True, oob_score=False, n_jobs=1,
              random_state=None, verbose=0))]
# iterate over the models
for m in models:
    # Train each of the models on the training set
    m[1].fit(xTrain, yTrain)
    # array of predictions on the test set
    pred = m[1].predict(xTest)
    # hit-rate and the confusion matrix for each model
    print("%s:\n%0.3f" % (m[0], m[1].score(xTest, yTest)))
    print("%s\n" % confusion_matrix(pred, yTest))

"""	                    Actual class
                            P 	N
    Predicted class    P	TP	FP
                       N	FN	TN

"""

rfc = RandomForestClassifier(
              n_estimators=1000, criterion='gini',
              max_depth=None, min_samples_split=2,
              min_samples_leaf=1, max_features='auto',
              bootstrap=True, oob_score=False, n_jobs=1,
              random_state=None, verbose=0).fit(xTrain, yTrain)

pd.set_option('float_format', '{:f}'.format)

train_pred = rfc.predict(xTrain)
rmse = np.sqrt(mean_squared_error(yTrain, train_pred))
print("RMSE_train: %f" % (rmse))
print('Train prediction values:')
train_pred = pd.DataFrame(train_pred); 
train_pred.rename(columns = {0: 'TrainPrediction'}, inplace=True); 
print(train_pred);print()

pd.set_option('float_format', '{:f}'.format)
test_pred = rfc.predict(xTest)
rmse = np.sqrt(mean_squared_error(yTest, test_pred))
print("RMSE_test: %f" % (rmse))
print('Test prediction values:')
test_pred = pd.DataFrame(test_pred)
test_pred.rename(columns = {0: 'TestPrediction'}, inplace=True); 
actual = pd.DataFrame(yTest)
actual.rename(columns = {0: 'Actual PriceDiff'}, inplace=True); 
compare = pd.concat([actual, test_pred], 1)
print(compare)