# Class for experimenting various single input DL models at word level
#
# arguments:
#   modelName       name of the model to be used into ['lstm', 'bidLstm', 'cnn', 'cudnngru', 'cudnnlstm']
#   use-holdout     use the holdout to limit the training and generate prediction on holdout set
#   fold-count      number of folds for k-fold training (default is 1)
#

import pandas as pd
import numpy as np
import pandas as pd
import sys, os
import argparse
import math

from keras import backend as K
from keras.engine.topology import Layer
from keras import initializers, regularizers, constraints
from keras.models import Model, load_model
from keras.layers import Dense, Embedding, Input, concatenate
from keras.layers import LSTM, Bidirectional, Dropout, SpatialDropout1D, AveragePooling1D, GlobalAveragePooling1D, TimeDistributed, Masking, Lambda 
from keras.layers import GRU, MaxPooling1D, Conv1D, GlobalMaxPool1D, Activation, Add, Flatten, BatchNormalization
from keras.layers import CuDNNGRU, CuDNNLSTM
from keras.optimizers import RMSprop, Adam, Nadam
from keras.preprocessing import text, sequence
from keras.callbacks import EarlyStopping, ModelCheckpoint

from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import train_test_split

#import utilities.Attention
from utilities.Attention import Attention
#from ToxicAttentionAlternative import AttentionAlternative
#from ToxicAttentionWeightedAverage import AttentionWeightedAverage

# seed is fixed for reproducibility
from numpy.random import seed
seed(7)
from tensorflow import set_random_seed
set_random_seed(8)

modelNames = ['lstm', 'bidLstm_simple', 'bidLstm', 'cnn', 'cnn2', 'cnn3', 'cudnngru', 'cudnnlstm', 'mix1', 'dpcnn', 'conv', 
    'cudnngru_simple', "gru", "gru_simple", 'lstm_cnn', 'han']

# parameters of the different DL models
parameters_lstm = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 40,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'LSTM.csv'
}

parameters_bidLstm_simple = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 25,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 300,
    'dense_size': 256,
    'resultFile': 'BidLSTM_simple.csv'
}

parameters_bidLstm = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 25,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 300,
    'dense_size': 256,
    'resultFile': 'BidLSTM_attention.csv'
}

parameters_cnn = {
    'max_features': 200000,
    'maxlen': 250,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'CNN.csv'
}

parameters_cnn2 = {
    'max_features': 200000,
    'maxlen': 250,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'CNN2.csv'
}

parameters_cnn3 = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'CNN3.csv'
}

parameters_lstm_cnn = {
    'max_features': 200000,
    'maxlen': 250,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'LSTM_CNN.csv'
}

parameters_conv = {
    'max_features': 200000,
    'maxlen': 250,
    'embed_size': 300,
    'epoch': 25,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 256,
    'dense_size': 64,
    'resultFile': 'CNN.csv'
}

parameters_cudnngru = {
    'max_features': 245000,
    'maxlen': 500,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 512,
    'dropout_rate': 0.5,
    'recurrent_dropout_rate': 0.5,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'CuDNNGRU.csv'
}

parameters_cudnngru_old = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 25,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'CuDNNGRU.csv'
}

parameters_cudnngru_simple = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 25,
    'batch_size': 256,
    'dropout_rate': 0.5,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'CuDNNGRU_simple.csv'
}

parameters_gru = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'GRU.csv'
}

parameters_gru_old = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 512,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'GRU.csv'
}

parameters_gru_simple = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 512,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'GRU_simple.csv'
}

parameters_cudnnlstm = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 25,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'CuDNNLSTM.csv'
}

parameters_mix1 = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 30,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'mix1.csv'
}

parameters_dpcnn = {
    'max_features': 200000,
    'maxlen': 300,
    'embed_size': 300,
    'epoch': 25,
    'batch_size': 256,
    'dropout_rate': 0.3,
    'recurrent_dropout_rate': 0.3,
    'recurrent_units': 64,
    'dense_size': 32,
    'resultFile': 'dpcnn.csv'
}

parametersMap = { 'lstm' : parameters_lstm, 'bidLstm_simple' : parameters_bidLstm_simple, 'bidLstm': parameters_bidLstm, 
                  'cnn': parameters_cnn, 'cnn2': parameters_cnn2, 'cnn3': parameters_cnn3, 'lstm_cnn': parameters_lstm_cnn,
                  'cudnngru': parameters_cudnngru, 'cudnnlstm': parameters_cudnnlstm, 'mix1': parameters_mix1, 
                  'gru': parameters_gru, 'gru_simple': parameters_gru_simple, 'dpcnn': parameters_dpcnn, 'conv': parameters_conv, 
                  'cudnngru_simple': parameters_cudnngru_simple }

# basic LSTM
def lstm(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix],
                  trainable=False)(inp)
    x = LSTM(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate)(x)
    #x = CuDNNLSTM(recurrent_units, return_sequences=True)(x)
    x = Dropout(dropout_rate)(x)
    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    #x_c = AttentionWeightedAverage()(x)
    #x_a = MaxPooling1D(pool_size=2)(x)
    #x_b = AveragePooling1D(pool_size=2)(x)
    x = concatenate([x_a,x_b])
    x = Dense(dense_size, activation="relu")(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(6, activation="sigmoid")(x)
    model = Model(inputs=inp, outputs=x)
    model.summary()
    model.compile(loss='binary_crossentropy', 
                optimizer='adam', 
                metrics=['accuracy'])
    return model

# bidirectional LSTM 
def bidLstm_simple(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=False)(inp)
    x = Bidirectional(LSTM(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate))(x)
    x = Dropout(dropout_rate)(x)
    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    #x_c = AttentionWeightedAverage()(x)
    #x_a = MaxPooling1D(pool_size=2)(x)
    #x_b = AveragePooling1D(pool_size=2)(x)
    x = concatenate([x_a,x_b])
    x = Dense(dense_size, activation="relu")(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(6, activation="sigmoid")(x)
    model = Model(inputs=inp, outputs=x)
    model.summary()
    model.compile(loss='binary_crossentropy', 
        optimizer='adam', 
        metrics=['accuracy'])
    return model

# bidirectional LSTM with attention layer
def bidLstm(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=False)(inp)
    x = Bidirectional(LSTM(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate))(x)
    #x = Dropout(dropout_rate)(x)
    x = Attention(maxlen)(x)
    #x = AttentionWeightedAverage(maxlen)(x)
    #print('len(x):', len(x))
    #x = AttentionWeightedAverage(maxlen)(x)
    x = Dense(dense_size, activation="relu")(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(6, activation="sigmoid")(x)
    model = Model(inputs=inp, outputs=x)
    model.summary()
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model


# conv+GRU with embeddings
def cnn(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=False)(inp)
    x = Dropout(dropout_rate)(x) 
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = GRU(recurrent_units)(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(dense_size, activation="relu")(x)
    x = Dense(6, activation="sigmoid")(x)
    model = Model(inputs=inp, outputs=x)
    model.summary()  
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

def cnn2_best(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=False)(inp)
    x = Dropout(dropout_rate)(x) 
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    #x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    #x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    #x = MaxPooling1D(pool_size=2)(x)
    x = GRU(recurrent_units, return_sequences=False, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate)(x)
    #x = Dropout(dropout_rate)(x)
    x = Dense(dense_size, activation="relu")(x)
    x = Dense(6, activation="sigmoid")(x)
    model = Model(inputs=inp, outputs=x)
    model.summary()  
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

def cnn2(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=False)(inp)
    x = Dropout(dropout_rate)(x) 
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    #x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    #x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    #x = MaxPooling1D(pool_size=2)(x)
    x = GRU(recurrent_units, return_sequences=False, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate)(x)
    #x = Dropout(dropout_rate)(x)
    x = Dense(dense_size, activation="relu")(x)
    x = Dense(6, activation="sigmoid")(x)
    model = Model(inputs=inp, outputs=x)
    model.summary()  
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

def cnn3(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=False)(inp)
    x = GRU(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate)(x)
    #x = Dropout(dropout_rate)(x) 

    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    #x_c = AttentionWeightedAverage()(x)
    #x_a = MaxPooling1D(pool_size=2)(x)
    #x_b = AveragePooling1D(pool_size=2)(x)
    x = concatenate([x_a,x_b])
    #x = Dropout(dropout_rate)(x)
    x = Dense(dense_size, activation="relu")(x)
    x = Dense(6, activation="sigmoid")(x)
    model = Model(inputs=inp, outputs=x)
    model.summary()  
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

def conv(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    filter_kernels = [7, 7, 5, 5, 3, 3]
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=False)(inp)
    conv = Conv1D(nb_filter=recurrent_units, filter_length=filter_kernels[0], border_mode='valid', activation='relu')(x)
    conv = MaxPooling1D(pool_length=3)(conv)
    conv1 = Conv1D(nb_filter=recurrent_units, filter_length=filter_kernels[1], border_mode='valid', activation='relu')(conv)
    conv1 = MaxPooling1D(pool_length=3)(conv1)
    conv2 = Conv1D(nb_filter=recurrent_units, filter_length=filter_kernels[2], border_mode='valid', activation='relu')(conv1)
    conv3 = Conv1D(nb_filter=recurrent_units, filter_length=filter_kernels[3], border_mode='valid', activation='relu')(conv2)
    conv4 = Conv1D(nb_filter=recurrent_units, filter_length=filter_kernels[4], border_mode='valid', activation='relu')(conv3)
    conv5 = Conv1D(nb_filter=recurrent_units, filter_length=filter_kernels[5], border_mode='valid', activation='relu')(conv4)
    conv5 = MaxPooling1D(pool_length=3)(conv5)
    conv5 = Flatten()(conv5)
    z = Dropout(0.5)(Dense(dense_size, activation='relu')(conv5))
    #x = GlobalMaxPool1D()(x)
    x = Dense(6, activation="sigmoid")(z)
    model = Model(inputs=inp, outputs=x)
    model.summary()  
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

# LSTM + conv
def lstm_cnn(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    inp = Input(shape=(maxlen, ))
    x = Embedding(max_features, embed_size, weights=[embedding_matrix],
                  trainable=False)(inp)
    x = LSTM(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate)(x)
    x = Dropout(dropout_rate)(x)

    x = Conv1D(filters=recurrent_units, kernel_size=2, padding='same', activation='relu')(x)
    x = Conv1D(filters=300,
                       kernel_size=5,
                       padding='valid',
                       activation='tanh',
                       strides=1)(x)
    #x = MaxPooling1D(pool_size=2)(x)

    #x = Conv1D(filters=300,
    #                   kernel_size=5,
    #                   padding='valid',
    #                   activation='tanh',
    #                   strides=1)(x)
    #x = MaxPooling1D(pool_size=2)(x)

    #x = Conv1D(filters=300,
    #                   kernel_size=3,
    #                   padding='valid',
    #                   activation='tanh',
    #                   strides=1)(x)

    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    x = concatenate([x_a,x_b])

    x = Dense(dense_size, activation="relu")(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(6, activation="sigmoid")(x)
    model = Model(inputs=inp, outputs=x)
    model.summary()
    model.compile(loss='binary_crossentropy', 
                optimizer='adam', 
                metrics=['accuracy'])
    return model

# CUDNNGRU simple
def cudnngru_simple(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size,embedding_matrix):
    input_layer = Input(shape=(maxlen,))
    embedding_layer = Embedding(max_features, embed_size,
                                weights=[embedding_matrix], trainable=False)(input_layer)
    x = Bidirectional(CuDNNGRU(recurrent_units, return_sequences=True))(embedding_layer)
    x = Dropout(dropout_rate)(x)
    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    #x = AttentionWeightedAverage(maxlen)(x)
    x = concatenate([x_a,x_b])
    x = Dense(dense_size, activation="relu")(x)
    output_layer = Dense(6, activation="sigmoid")(x)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.summary()
    model.compile(loss='binary_crossentropy',
                  #optimizer=RMSprop(clipvalue=1, clipnorm=1),
                  optimizer=Adam(lr=0.001),
                  #optimizer=Nadam(lr=0.001),
                  metrics=['accuracy'])
    return model

# 2 bid. CUDNNGRU 
def cudnngru(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size,embedding_matrix):
    input_layer = Input(shape=(maxlen,))
    embedding_layer = Embedding(max_features, embed_size,
                                weights=[embedding_matrix], trainable=False)(input_layer)
    x = Bidirectional(CuDNNGRU(recurrent_units, return_sequences=True))(embedding_layer)
    x = Dropout(dropout_rate)(x)
    x = Bidirectional(CuDNNGRU(recurrent_units, return_sequences=False))(x)
    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    x = concatenate([x_a,x_b])
    #x = AttentionWeightedAverage(maxlen)(x)
    x = Dense(dense_size, activation="relu")(x)
    output_layer = Dense(6, activation="sigmoid")(x)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.summary()
    model.compile(loss='binary_crossentropy',
                  #optimizer=RMSprop(clipvalue=1, clipnorm=1),
                  optimizer='adam',
                  metrics=['accuracy'])
    return model

# 2 bid. GRU 
def gru(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size,embedding_matrix):
    input_layer = Input(shape=(maxlen,))
    embedding_layer = Embedding(max_features, embed_size,
                                weights=[embedding_matrix], trainable=False)(input_layer)
    x = Bidirectional(GRU(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=recurrent_dropout_rate))(embedding_layer)
    x = Dropout(dropout_rate)(x)
    x = Bidirectional(GRU(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=recurrent_dropout_rate))(x)
    #x = AttentionWeightedAverage(maxlen)(x)
    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    #x_c = AttentionWeightedAverage()(x)
    #x_a = MaxPooling1D(pool_size=2)(x)
    #x_b = AveragePooling1D(pool_size=2)(x)
    x = concatenate([x_a,x_b], axis=1)
    #x = Dense(dense_size, activation="relu")(x)
    #x = Dropout(dropout_rate)(x)
    x = Dense(dense_size, activation="relu")(x)
    output_layer = Dense(6, activation="sigmoid")(x)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.summary()
    model.compile(loss='binary_crossentropy',
                  #optimizer=RMSprop(clipvalue=1, clipnorm=1),
                  optimizer='adam',
                  metrics=['accuracy'])
    return model

def gru_best(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size,embedding_matrix):
    input_layer = Input(shape=(maxlen,))
    embedding_layer = Embedding(max_features, embed_size,
                                weights=[embedding_matrix], trainable=False)(input_layer)
    x = Bidirectional(GRU(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate))(embedding_layer)
    x = Dropout(dropout_rate)(x)
    x = Bidirectional(GRU(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate))(x)
    #x = AttentionWeightedAverage(maxlen)(x)
    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    #x_c = AttentionWeightedAverage()(x)
    #x_a = MaxPooling1D(pool_size=2)(x)
    #x_b = AveragePooling1D(pool_size=2)(x)
    x = concatenate([x_a,x_b], axis=1)
    #x = Dense(dense_size, activation="relu")(x)
    #x = Dropout(dropout_rate)(x)
    x = Dense(dense_size, activation="relu")(x)
    output_layer = Dense(6, activation="sigmoid")(x)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.summary()
    model.compile(loss='binary_crossentropy',
                  optimizer=RMSprop(clipvalue=1, clipnorm=1),
                  #optimizer='adam',
                  metrics=['accuracy'])
    return model

# 1 layer bid GRU
def gru_simple(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size,embedding_matrix):
    input_layer = Input(shape=(maxlen,))
    embedding_layer = Embedding(max_features, embed_size,
                                weights=[embedding_matrix], trainable=False)(input_layer)
    x = Bidirectional(GRU(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=dropout_rate))(embedding_layer)
    #x = AttentionWeightedAverage(maxlen)(x)
    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    #x_c = AttentionWeightedAverage()(x)
    #x_a = MaxPooling1D(pool_size=2)(x)
    #x_b = AveragePooling1D(pool_size=2)(x)
    x = concatenate([x_a,x_b], axis=1)
    #x = Dense(dense_size, activation="relu")(x)
    #x = Dropout(dropout_rate)(x)
    x = Dense(dense_size, activation="relu")(x)
    output_layer = Dense(6, activation="sigmoid")(x)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.summary()
    model.compile(loss='binary_crossentropy',
                  optimizer=RMSprop(clipvalue=1, clipnorm=1),
                  #optimizer='adam',
                  metrics=['accuracy'])
    return model

# 2 layers bid CUDNNLSTM
def cudnnlstm(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    input_layer = Input(shape=(maxlen,))
    embedding_layer = Embedding(max_features, embed_size,
                                weights=[embedding_matrix], trainable=False)(input_layer)
    x = Bidirectional(CuDNNLSTM(recurrent_units, return_sequences=True))(embedding_layer)
    x = Dropout(dropout_rate)(x)
    x = Bidirectional(CuDNNLSTM(recurrent_units, return_sequences=False))(x)
    x = Dense(dense_size, activation="relu")(x)
    output_layer = Dense(6, activation="sigmoid")(x)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.summary()
    model.compile(loss='binary_crossentropy',
                  optimizer=RMSprop(clipvalue=1, clipnorm=1),
                  #optimizer='adam',
                  metrics=['accuracy'])
    return model

# bid CUDNNGRU + bid CUDNNLSTM
def mix1(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    input_layer = Input(shape=(maxlen,))
    embedding_layer = Embedding(max_features, embed_size,
                                weights=[embedding_matrix], trainable=False)(input_layer)
    x = Bidirectional(GRU(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=recurrent_dropout_rate))(embedding_layer)
    x = Dropout(dropout_rate)(x)
    x = Bidirectional(LSTM(recurrent_units, return_sequences=True, dropout=dropout_rate,
                           recurrent_dropout=recurrent_dropout_rate))(x)

    x_a = GlobalMaxPool1D()(x)
    x_b = GlobalAveragePooling1D()(x)
    x = concatenate([x_a,x_b])

    x = Dense(dense_size, activation="relu")(x)
    output_layer = Dense(6, activation="sigmoid")(x)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.summary()
    model.compile(loss='binary_crossentropy',
                  optimizer=RMSprop(clipvalue=1, clipnorm=1),
                  #optimizer='adam',
                  metrics=['accuracy'])
    return model

# DPCNN
def dpcnn(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_matrix):
    input_layer = Input(shape=(maxlen, ))
    X = Embedding(max_features, embed_size, weights=[embedding_matrix], 
                  trainable=False)(input_layer)
    # first block
    X_shortcut1 = X
    X = Conv1D(filters=recurrent_units, kernel_size=2, strides=3)(X)
    X = Activation('relu')(X)
    X = Conv1D(filters=recurrent_units, kernel_size=2, strides=3)(X)
    X = Activation('relu')(X)

    # connect shortcut to the main path
    X = Activation('relu')(X_shortcut1)  # pre activation
    X = Add()([X_shortcut1,X])
    X = MaxPooling1D(pool_size=3, strides=2, padding='valid')(X)

    # second block
    X_shortcut2 = X
    X = Conv1D(filters=recurrent_units, kernel_size=2, strides=3)(X)
    X = Activation('relu')(X)
    X = Conv1D(filters=recurrent_units, kernel_size=2, strides=3)(X)
    X = Activation('relu')(X)

    # connect shortcut to the main path
    X = Activation('relu')(X_shortcut2)  # pre activation
    X = Add()([X_shortcut2,X])
    X = MaxPooling1D(pool_size=2, strides=2, padding='valid')(X)

    # Output
    X = Flatten()(X)
    X = Dense(6, activation='sigmoid')(X)

    model = Model(inputs = input_layer, outputs = X, name='dpcnn')
    model.summary()
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model


def getModel(modelName):
    if (modelName == 'bidLstm'):
        model = bidLstm(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'bidLstm_simple'):
        model = bidLstm_simple(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'lstm'):
        model = lstm(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'cnn'):
        model = cnn(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'cnn2'):
        model = cnn2(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'cnn3'):
        model = cnn3(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'lstm_cnn'):
        model = lstm_cnn(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'conv'):
        model = dpcnn(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'cudnngru'):
        model = cudnngru(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'cudnngru_simple'):
        model = cudnngru_simple(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'cudnnlstm'):
        model = cudnnlstm(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'mix1'):
        model = mix1(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'dpcnn'):
        model = dpcnn(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'gru'):
        model = gru(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    if (modelName == 'gru_simple'):
        model = gru_simple(maxlen, max_features, embed_size, recurrent_units, dropout_rate, recurrent_dropout_rate, dense_size, embedding_vector)
    return model


def train_model(model, batch_size, max_epoch, train_x, train_y, val_x, val_y):
    best_loss = -1
    best_roc_auc = -1
    best_weights = None
    best_epoch = 0
    current_epoch = 0

    while current_epoch <= max_epoch:
        model.fit(train_x, train_y, batch_size=batch_size, epochs=1)
        y_pred = model.predict(val_x, batch_size=batch_size)

        total_loss = 0.0
        total_roc_auc = 0.0
        for j in range(len(list_classes)):
            loss = log_loss(val_y[:, j], y_pred[:, j])
            total_loss += loss
            roc_auc = roc_auc_score(val_y[:, j], y_pred[:, j])
            total_roc_auc += roc_auc

        total_loss /= len(list_classes)
        total_roc_auc /= len(list_classes)
        print("Epoch {0} loss {1} best_loss {2} (for info) ".format(current_epoch, total_loss, best_loss))
        print("Epoch {0} roc_auc {1} best_roc_auc {2} (for early stop) ".format(current_epoch, total_roc_auc, best_roc_auc))

        current_epoch += 1
        if total_loss < best_loss or best_loss == -1 or math.isnan(best_loss) is True:
            best_loss = total_loss

        if total_roc_auc > best_roc_auc or best_roc_auc == -1:
            best_roc_auc = total_roc_auc
            best_weights = model.get_weights()
            best_epoch = current_epoch
        else:
            if current_epoch - best_epoch == 5:
                break

    model.set_weights(best_weights)
    return model, best_roc_auc


def train_folds(X, y, fold_count, batch_size, max_epoch, modelName):
    fold_size = len(X) // fold_count
    models = []
    roc_scores = []
    for fold_id in range(0, fold_count):
        print('\n------------------------ fold ' + str(fold_id) + '--------------------------------------')
        fold_start = fold_size * fold_id
        fold_end = fold_start + fold_size

        if fold_id == fold_size - 1:
            fold_end = len(X)

        train_x = np.concatenate([X[:fold_start], X[fold_end:]])
        train_y = np.concatenate([y[:fold_start], y[fold_end:]])

        val_x = X[fold_start:fold_end]
        val_y = y[fold_start:fold_end]

        foldModel, best_roc_auc = train_model(getModel(modelName), batch_size, max_epoch, train_x, train_y, val_x, val_y)
        models.append(foldModel)
        
        #model_path = os.path.join("../data/models/",modelName+".model{0}_weights.hdf5".format(fold_id))
        #foldModel.save_weights(model_path, foldModel.get_weights())
        #foldModel.save(model_path)
        #del foldModel

        roc_scores.append(best_roc_auc)
    all_roc_scores = sum(roc_scores)
    print("Average best roc_auc scores over the", fold_count, "fold: ", all_roc_scores/fold_count)

    return models


def make_df(train_path, holdout_path, test_path, max_features, maxlen, list_classes):
    train_df = pd.read_csv(train_path)
    if (useHoldout):
        holdout_df = pd.read_csv(holdout_path)
    test_df = pd.read_csv(test_path)
    
    train_df.comment_text.fillna('MISSINGVALUE', inplace=True)
    if (useHoldout):
        holdout_df.comment_text.fillna('MISSINGVALUE', inplace=True)
    test_df.comment_text.fillna('MISSINGVALUE', inplace=True)
    
    """
    extra_train_df = pd.read_csv('../data/eval/holdout-test.part.csv')
    extra_train_df = extra_train_df.drop('comment_text', 1)
    extra_train_df = pd.merge(test_df, extra_train_df, how='inner', on=['id'])
    #print('extra_train_df.shape:', extra_train_df.shape)
    #print('extra_train_df:', extra_train_df)

    #print('train_df.shape:', train_df.shape)

    train_df = pd.concat([train_df, extra_train_df], axis=0)
    """
    train_df = train_df.sample(frac=1)
    
    #print('train_df.shape:', train_df.shape)
    #print('train_df:', train_df)
    
    list_sentences_train = train_df["comment_text"].values
    y = train_df[list_classes].values
    if (useHoldout):
        list_sentences_holdout = holdout_df["comment_text"].values
    list_sentences_test = test_df["comment_text"].values

    if (useHoldout):
        list_sentences_all = np.concatenate([list_sentences_train, list_sentences_holdout, list_sentences_test])
    else:
        list_sentences_all = np.concatenate([list_sentences_train, list_sentences_test])

    tokenizer = text.Tokenizer(num_words=max_features)
    tokenizer.fit_on_texts(list(list_sentences_all))
    print('word_index size:', len(tokenizer.word_index))

    list_tokenized_train = tokenizer.texts_to_sequences(list_sentences_train)
    if (useHoldout):
        list_tokenized_holdout = tokenizer.texts_to_sequences(list_sentences_holdout)
    list_tokenized_test = tokenizer.texts_to_sequences(list_sentences_test)
    
    X_t = sequence.pad_sequences(list_tokenized_train, maxlen=maxlen)
    if (useHoldout):
        X_h = sequence.pad_sequences(list_tokenized_holdout, maxlen=maxlen)
    else:
        X_h = None
    X_te = sequence.pad_sequences(list_tokenized_test, maxlen=maxlen)
    word_index = tokenizer.word_index

    return X_t, X_h, X_te, y, word_index


