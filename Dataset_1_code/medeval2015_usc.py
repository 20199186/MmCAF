# -*- coding: utf-8 -*-
"""medeval2015_bert_efficientnet_average.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/125wztxnuJCHt6DD1b7wdYHPcMaTVZWxQ
"""

#!pip install -q tensorflow_text
print("USE_Epoch2")
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text
from tensorflow import keras

label_map = {"fake": 0, "real": 1, "humor": 2}

#from google.colab import drive
#drive.mount('/content/drive', force_remount=True)
import sys
import subprocess
subprocess.check_call([sys.executable, '-m','pip', 'install', 'xlrd'])
#!pip install --upgrade xlrd

image_base_path = (
    '/scratch/satyendrac.mnitjaipur/data/monika/dataset/medeval2015/all_imgs_medeval2015_dev/'
)

df = pd.read_excel(
    '/scratch/satyendrac.mnitjaipur/data/monika/dataset/medeval2015/dev_medeval2015_modified2.xls'
)
df

#images_two_paths = []



# Create another column containing the integer ids of
# the string labels.
df["label_idx"] = df["label"].apply(lambda x: label_map[x])

#from pathlib import Path
#names = []
#data_dir = '/content/drive/MyDrive/medeval2015_fromserver/all_imgs_medeval2015_dev/'
#for filepath in Path(data_dir).rglob("*"):
#       if f"{filepath}".endswith('.jpg'):
#           names.append(f"{filepath}")

##print(names)
#print(len(names))

#names1 = []
#for line in df['image_1_path']:
#    if line not in names:
#      names1.append(line)

#print(names1)
#print(len(names1))

df.drop(df[(df.tweetId ==265203067912347650)].index,inplace = True)
df.drop(df[(df.tweetId ==263312347991511041)].index,inplace = True)
df.drop(df[(df.tweetId ==263043345880870913)].index,inplace = True)
df.drop(df[(df.tweetId ==263110145536581632)].index,inplace = True)
df.drop(df[(df.tweetId ==324315545572896768)].index,inplace = True)
df.drop(df[(df.tweetId ==324513597852098561)].index,inplace = True)
df.drop(df[(df.tweetId ==324569471253630976)].index,inplace = True)

#print(df.iloc[13224,3])
#z = df[(df.tweetId ==324569471253630976)].index
#print(z)
#y = df[(df.userId == 812812238)].index
#print(y)
#print("z[0]", z)

#visualize(random_idx)
            
df["label"].value_counts()

train_df, test_df = train_test_split(
    df, test_size=0.2, stratify=df["label"].values, random_state=42
)
# 5% for validation
train_df, val_df = train_test_split(
    train_df, test_size=0.05, stratify=train_df["label"].values, random_state=42
)

print(f"Total training examples: {len(train_df)}")
print(f"Total validation examples: {len(val_df)}")
print(f"Total test examples: {len(test_df)}")

# Define TF Hub paths to the BERT encoder and its preprocessor
def dataframe_to_dataset(dataframe):
    columns = ["tweetText","label_idx"]
    dataframe = dataframe[columns].copy()
    labels = dataframe.pop("label_idx")
    ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
    ds = ds.shuffle(buffer_size=len(dataframe))
    return ds

resize = (128, 128)




def preprocess_text(text_1):
#    text_1 = tf.convert_to_tensor([text_1])
#    output = roberta_preprocess_model([text_1])
#    output = {feature: tf.squeeze(output[feature]) for feature in roberta_input_features}
     output=text_1
     return output


def preprocess_text_and_image(sample):
    text = preprocess_text(sample["tweetText"])
    return {"text": text}

batch_size = 32
auto = tf.data.AUTOTUNE


def prepare_dataset(dataframe, training=True):
    ds = dataframe_to_dataset(dataframe)
    if training:
        ds = ds.shuffle(len(train_df))
    ds = ds.map(lambda x,y: (preprocess_text_and_image(x),y)).cache()
    ds = ds.batch(batch_size).prefetch(auto)
    return ds


train_ds = prepare_dataset(train_df)
validation_ds = prepare_dataset(val_df, False)
test_ds = prepare_dataset(test_df, False)

train_ds

def project_embeddings(
    embeddings, num_projection_layers, projection_dims, dropout_rate
):
    projected_embeddings = keras.layers.Dense(units=projection_dims)(embeddings)
    for _ in range(num_projection_layers):
        x = tf.nn.gelu(projected_embeddings)
        x = keras.layers.Dense(projection_dims)(x)
        x = keras.layers.Dropout(dropout_rate)(x)
        x = keras.layers.Add()([projected_embeddings, x])
        projected_embeddings = keras.layers.LayerNormalization()(x)
    return projected_embeddings

#from tensorflow.keras.applications.inception_v3 import InceptionV3
#from tensorflow.keras.applications.inception_v3 import preprocess_input
   #inception = keras.applications.InceptionV3(include_top=False, weights="imagenet", pooling="avg")
    # Set the trainability of the base encoder.

from tensorflow.keras import layers
def create_text_encoder(
    num_projection_layers, projection_dims, dropout_rate, trainable=False
):
    sentence_encoder_layer = hub.KerasLayer("/scratch/satyendrac.mnitjaipur/data/monika/embedding/universal-sentence-encoder/")
    inputs = layers.Input(shape=(),dtype=tf.string,name="text")
    output = sentence_encoder_layer(inputs)
    # Load the pre-trained BERT model to be used as the base encoder.
    #roberta = hub.KerasLayer(roberta_model_path, name="roberta",)
    # Set the trainability of the base encoder.
    #roberta.trainable = trainable

    # Receive the text as inputs.
    #roberta_input_features = ["input_type_ids", "input_mask", "input_word_ids"]
    #inputs = {
    #    feature: keras.Input(shape=(128,), dtype=tf.int32, name=feature)
    #    for feature in roberta_input_features
    #}

    # Generate embeddings for the preprocessed text using the BERT model.
    #embeddings = roberta(inputs)["pooled_output"]

    # Project the embeddings produced by the model.
    outputs = project_embeddings(
        output, num_projection_layers, projection_dims, dropout_rate
    )
    # Create the text encoder model.
    return keras.Model(inputs, outputs, name="text_encoder")

def create_multimodal_model(
    num_projection_layers=1,
    projection_dims=256,
    dropout_rate=0.1,
    vision_trainable=False,
    text_trainable=False,
):
    # Receive the images as inputs.
    #image_2 = keras.Input(shape=(128, 128, 3), name="image_2")

    # Receive the text as inputs.
    #roberta_input_features = ["input_type_ids", "input_mask", "input_word_ids"]
    #text_inputs = {
    #    feature: keras.Input(shape=(128,), dtype=tf.int32, name=feature)
    #    for feature in roberta_input_features
    #}
    text_inputs = keras.Input(shape=(), dtype=tf.string,name="text")

    # Create the encoders.
    text_encoder = create_text_encoder(
        num_projection_layers, projection_dims, dropout_rate, text_trainable
    )

    # Fetch the embedding projections.
    text_projections = text_encoder(text_inputs)

    # Concatenate the projections and pass through the classification layer.
    #average = keras.layers.Average()([vision_projections, text_projections])
    outputs = keras.layers.Dense(3, activation="softmax")(text_projections)
    return keras.Model([text_inputs], outputs)


multimodal_model = create_multimodal_model()
#keras.utils.plot_model(multimodal_model, show_shapes=True)

#image_2 = keras.Input(shape=(128, 128, 3), name="image_2")


text_inputs = keras.Input(shape=(), dtype=tf.string, name="text")
print(text_inputs)
text_encoder = create_text_encoder(
       1, 256, 0.1, False)
text_projections = text_encoder(text_inputs)
print(text_projections)

#text_inputs = {
#        feature: keras.Input(shape=(128,), dtype=tf.int32, name=feature)
#        for feature in roberta_input_features
#    }
#print(text_inputs)
#text_encoder = create_text_encoder(
#       1, 256, 0.1, False)
#text_projections = text_encoder(text_inputs)
#print(text_projections)

multimodal_model.compile(
    optimizer="adam", loss="sparse_categorical_crossentropy", metrics= "accuracy"
)

#from keras.callbacks import ModelCheckpoint, EarlyStopping
#es = EarlyStopping(monitor='val_loss', mode='min', verbose=1)
# fit model
history = multimodal_model.fit(train_ds, validation_data=validation_ds, epochs=2)

model_history = pd.DataFrame(history.history)
model_history['epoch'] = history.epoch

fig, ax = plt.subplots(1, figsize=(8,6))
num_epochs = model_history.shape[0]

ax.plot(np.arange(0, num_epochs), model_history["accuracy"], 
        label="Training Accuracy")
ax.plot(np.arange(0, num_epochs), model_history["val_accuracy"], 
        label="Validation Accuracy")
ax.legend()
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.tight_layout()
plt.show()

print(model_history)

_, acc = multimodal_model.evaluate(test_ds)
print(f"Accuracy on the test set: {round(acc * 100, 2)}%.")

from sklearn.metrics import classification_report, confusion_matrix
y_pred = multimodal_model.predict(test_ds)

predicted_categories = tf.argmax(y_pred, axis=1)

true_categories = tf.concat([y for x, y in test_ds], axis=0)

confusion_matrix(predicted_categories, true_categories)

print(classification_report(true_categories, predicted_categories, target_names=label_map, digits=4))