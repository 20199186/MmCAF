# -*- coding: utf-8 -*-
"""ticnn_bert_efficientnet_average.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UchK0_aof-p2p-ndtTHThpPPbvGow7XQ
"""
print("ticnn usc efficientnet avergae")


#!pip install -q tensorflow_text

from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text
from tensorflow import keras

label_map = {"fake": 0, "real": 1}

#from google.colab import drive
#drive.mount('/content/drive')

image_base_path = (
    '/scratch/satyendrac.mnitjaipur/data/monika/dataset/ticnn/ticnn/images/all_imgs/'
)

df = pd.read_csv(
    '/scratch/satyendrac.mnitjaipur/data/monika/dataset/ticnn/ticnn/ticnn_modified_dataset_7063.csv'
)
df.sample(5)

#df = df[:100]

images_one_paths = []
#images_two_paths = []


for idx in range(len(df)):
    current_row = df.iloc[idx]
    uid = current_row["u_id_custom"]
    #userid=current_row["userId"]
    #imageid=current_row["imageId(s)"]
    #id_2 = current_row["id_2"]
    extentsion_one = current_row["images_path"].split(".")[-1]
    #print(extentsion_one)
    #extentsion_two = current_row["image_2"].split(".")[-1]

    image_one_path = os.path.join(image_base_path, str(uid) + str("_")+f".{extentsion_one}")
    #image_two_path = os.path.join(image_base_path, str(id_2) + f".{extentsion_two}")

    images_one_paths.append(image_one_path)
    #images_two_paths.append(image_two_path)

df["image_1_path"] = images_one_paths
#print(df["image_1_path"])

#df["image_2_path"] = images_two_paths

# Create another column containing the integer ids of
# the string labels.
df["label_idx"] = df["type"].apply(lambda x: label_map[x])

print(df)

from pathlib import Path
names = []
data_dir = '/scratch/satyendrac.mnitjaipur/data/monika/dataset/ticnn/ticnn/images/all_imgs/'
for filepath in Path(data_dir).rglob("*"):
       if f"{filepath}".endswith('.jpg'):
           names.append(f"{filepath}")

print(len(names))

names1 = []
x = []
for line in df['image_1_path']:
    if line not in names:
       i = df[(df.image_1_path == line)].index
       df.drop(i[0], inplace = True)
       #x.append([(df.image_1_path == line)].index)
       #names1.append(line)

def visualize(idx):
    current_row = df.iloc[idx]
    image_1 = plt.imread(current_row["image_1_path"])
    #image_2 = plt.imread(current_row["image_2_path"])
    text_1 = current_row["text"]
    #text_2 = current_row["text_2"]
    label = current_row["type"]

    plt.subplot(1, 2, 1)
    plt.imshow(image_1)
    plt.axis("off")
    plt.title("Image One")
    #plt.subplot(1, 2, 2)
    #plt.imshow(image_1)
    #plt.axis("off")
    #plt.title("Image Two")
    plt.show()

    print(f"Text one: {text_1}")
    #print(f"Text two: {text_2}")
    print(f"Label: {label}")


random_idx = np.random.choice(len(df))
visualize(random_idx)

#random_idx = np.random.choice(len(df))
#visualize(random_idx)

df["type"].value_counts()

# 10% for test
train_df, test_df = train_test_split(
    df, test_size=0.1, stratify=df["type"].values, random_state=42
)
# 5% for validation
train_df, val_df = train_test_split(
    train_df, test_size=0.3, stratify=train_df["type"].values, random_state=42
)

print(f"Total training examples: {len(train_df)}")
print(f"Total validation examples: {len(val_df)}")
print(f"Total test examples: {len(test_df)}")

# Define TF Hub paths to the BERT encoder and its preprocessor
#bert_model_path = (
#    "/scratch/satyendrac.mnitjaipur/data/monika/embedding/small_bert_bert_en_uncased_L-2_H-256_A-4_2/"
#)
#bert_preprocess_path = "/scratch/satyendrac.mnitjaipur/data/monika/embedding/bert_en_uncased_preprocess_3"
#roberta_preprocess_path = "/scratch/satyendrac.mnitjaipur/data/monika/embedding/roberta/preprocess/"
#roberta_model_path = "/scratch/satyendrac.mnitjaipur/data/monika/embedding/roberta/model/"

#keras.utils.plot_model(bert_preprocess_model, show_shapes=True, show_dtype=True)

def dataframe_to_dataset(dataframe):
    columns = ["image_1_path",  "text","label_idx"]
    dataframe = dataframe[columns].copy()
    labels = dataframe.pop("label_idx")
    ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
    ds = ds.shuffle(buffer_size=len(dataframe))
    return ds

resize = (128, 128)


def preprocess_image(image_path):
    extension = tf.strings.split(image_path)[-1]
    print(extension)

    image = tf.io.read_file(image_path)
    if extension == b"jpg":
        image = tf.image.decode_jpeg(image, 3)
    else:
        image = tf.image.decode_png(image,3)   
    image = tf.image.resize(image, resize)
    return image


def preprocess_text(text_1):
    output = text_1
    return output


def preprocess_text_and_image(sample):
    image_1 = preprocess_image(sample["image_1_path"])
    text = preprocess_text(sample["text"])
    return {"image_1": image_1, "text": text}

batch_size = 32
auto = tf.data.AUTOTUNE


def prepare_dataset(dataframe, training=True):
    ds = dataframe_to_dataset(dataframe)
    if training:
        ds = ds.shuffle(len(train_df))
    ds = ds.map(lambda x, y: (preprocess_text_and_image(x), y)).cache()
    ds = ds.batch(batch_size).prefetch(auto)
    return ds


train_ds = prepare_dataset(train_df)
validation_ds = prepare_dataset(val_df, False)
test_ds = prepare_dataset(test_df, False)

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

from tensorflow.keras.applications import EfficientNetB7

def create_vision_encoder(
    num_projection_layers, projection_dims, dropout_rate, trainable=False
):
    # Load the pre-trained ResNet50V2 model to be used as the base encoder.
    efficientnetb7 = EfficientNetB7(input_shape=(128,128,3),include_top=False, weights="imagenet",pooling='max' )
    #resnet_v2 = keras.applications.ResNet50V2(include_top=False, weights="imagenet", pooling="avg")
    # Set the trainability of the base encoder.
    for layer in efficientnetb7.layers:
        layer.trainable = False

    # Receive the images as inputs.
    image_1 = keras.Input(shape=(128, 128, 3), name="image_1")
   # image_2 = keras.Input(shape=(128, 128, 3), name="image_2")

    
    # Preprocess the input image.
    preprocessed_1 = tf.keras.applications.efficientnet.preprocess_input(image_1)
  #  preprocessed_2 = tf.keras.applications.efficientnet.preprocess_input(image_2)

    # Generate the embeddings for the images using the resnet_v2 model
    # concatenate them.
    embeddings_1 = efficientnetb7(preprocessed_1)
   # embeddings_2 = efficientnetb7(preprocessed_2)
    embeddings = keras.layers.Concatenate()([embeddings_1])

    # Project the embeddings produced by the model.
    outputs = project_embeddings(
        embeddings, num_projection_layers, projection_dims, dropout_rate
    )
    # Create the vision encoder model.
    return keras.Model([image_1], outputs, name="vision_encoder")


from tensorflow.keras import layers
def create_text_encoder(
    num_projection_layers, projection_dims, dropout_rate, trainable=False
):
    # Load the pre-trained BERT model to be used as the base encoder.
    sentence_encoder_layer = hub.KerasLayer("/scratch/satyendrac.mnitjaipur/data/monika/embedding/universal-sentence-encoder/")
    inputs = layers.Input(shape=(),dtype=tf.string,name="text")
    output = sentence_encoder_layer(inputs)
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
    image_1 = keras.Input(shape=(128, 128, 3), name="image_1")
    #image_2 = keras.Input(shape=(128, 128, 3), name="image_2")

    # Receive the text as inputs.
    #roberta_input_features = ["input_type_ids", "input_mask", "input_word_ids"]
    #text_inputs = {
    #    feature: keras.Input(shape=(128,), dtype=tf.int32, name=feature)
    #    for feature in roberta_input_features
    #}
    text_inputs = keras.Input(shape=(), dtype=tf.string,name="text")

    # Create the encoders.
    vision_encoder = create_vision_encoder(
        num_projection_layers, projection_dims, dropout_rate, vision_trainable
    )
    text_encoder = create_text_encoder(
        num_projection_layers, projection_dims, dropout_rate, text_trainable
    )

    # Fetch the embedding projections.
    vision_projections = vision_encoder([image_1])
    text_projections = text_encoder(text_inputs)

    # Concatenate the projections and pass through the classification layer.
    average = keras.layers.Average()([vision_projections, text_projections])
    outputs = keras.layers.Dense(3, activation="softmax")(average)
    return keras.Model([image_1, text_inputs], outputs)


multimodal_model = create_multimodal_model()
#keras.utils.plot_model(multimodal_model, show_shapes=True)
print(multimodal_model.summary())
vision_encoder = create_vision_encoder(1, 256, 0.1, False)
image_1 = keras.Input(shape=(128, 128, 3), name="image_1")
#image_2 = keras.Input(shape=(128, 128, 3), name="image_2")

vision_projections = vision_encoder([image_1])
vision_projections

text_inputs = keras.Input(shape=(), dtype=tf.string, name="text")   
print(text_inputs)
text_encoder = create_text_encoder(
       1, 256, 0.1, False)
text_projections = text_encoder(text_inputs)
print(text_projections)

multimodal_model.compile(
    optimizer="adam", loss="sparse_categorical_crossentropy", metrics="accuracy"
)

from keras.callbacks import ModelCheckpoint, EarlyStopping
es = EarlyStopping(monitor='val_loss', mode='min', verbose=1)
# fit model
import time

start = time.time()
history = multimodal_model.fit(train_ds, validation_data=validation_ds, epochs=10, verbose=0, callbacks=[es])
print("Total time: ", time.time() - start, "seconds")
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
