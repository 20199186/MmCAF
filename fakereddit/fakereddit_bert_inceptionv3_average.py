# -*- coding: utf-8 -*-
"""20Epoch_Fakereddit_bert_efficientnet_average.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12zG1dpcyf6K2tv_wwp45DYvOZle7JMoj
"""
print("fakereddit bert inceptionv3 average")
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

#from google.colab import drive
#drive.mount('/content/drive',force_remount=True)

image_base_path = (
    '/scratch/satyendrac.mnitjaipur/data/monika/dataset/fakereddit/fake_reddit_merged_dataset/'
)

import glob
import os

df = pd.read_csv('/scratch/satyendrac.mnitjaipur/data/monika/dataset/fakereddit/fakeredditmergedcsv.csv')
#files = glob.glob(files)
#print(len(files))
#df = pd.concat(map(pd.read_csv, files), ignore_index=True)

print(df)

df.sample(5)

images_one_paths = []
#images_two_paths = []


for idx in range(len(df)):
    current_row = df.iloc[idx]
    #uid = current_row["custom_uuid"]
    id=current_row["id"]
    #imageid=current_row["imageId(s)"]
    #id_2 = current_row["id_2"]
    extentsion_one = current_row["images"].split(".")[-1]
    #print(extentsion_one)
    #extentsion_two = current_row["image_2"].split(".")[-1]


    #image_one_path = os.path.join(image_base_path, str(uid) +f".{extentsion_one}")
    image_one_path = os.path.join(image_base_path + id + f".{extentsion_one}")
    #image_two_path = os.path.join(image_base_path, str(id_2) + f".{extentsion_two}")

    images_one_paths.append(image_one_path)
    #images_two_paths.append(image_two_path)
#print("images_one_paths", images_one_paths)
df["image_1_path"] = images_one_paths
#print(df)
#print(df["image_1_path"])

#df["image_2_path"] = images_two_paths

# Create another column containing the integer ids of
# the string labels.
df["label_idx"] = df["2_way_label"]

from pathlib import Path
names = []
data_dir = '/scratch/satyendrac.mnitjaipur/data/monika/dataset/fakereddit/fake_reddit_merged_dataset/'
for filepath in Path(data_dir).rglob("*"):
       if f"{filepath}".endswith('.jpg'):
           names.append(f"{filepath}")

#print(names)
print(len(names))

names1 = []
x = []
for line in df['image_1_path']:
    if line not in names:
       i = df[(df.image_1_path == line)].index
       df.drop(i[0], inplace = True)
       #print("dropped",line)
       #x.append([(df.image_1_path == line)].index)
       #names1.append(line)

print(df)

#print(line)
#i = df[(df.image_1_path == line)].index
#print(i[0])

#print(df.iloc[49381,6])

#print(names1)
#print(len(names1))

def visualize(idx):
    current_row = df.iloc[idx]
    image_1 = plt.imread(current_row["image_1_path"])
    #image_2 = plt.imread(current_row["image_2_path"])
    text_1 = current_row["clean_title"]
    #text_2 = current_row["text_2"]
    label = current_row["2_way_label"]

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


#random_idx = np.random.choice(len(df))
#visualize(random_idx)

#random_idx = np.random.choice(len(df))
#visualize(random_idx)

df["2_way_label"].value_counts()

# 10% for test
train_df, test_df = train_test_split(
    df, test_size=0.2, stratify=df["2_way_label"].values, random_state=42
)
# 5% for validation
train_df, val_df = train_test_split(
    train_df, test_size=0.05, stratify=train_df["2_way_label"].values, random_state=42
)

print(f"Total training examples: {len(train_df)}")
print(f"Total validation examples: {len(val_df)}")
print(f"Total test examples: {len(test_df)}")

# Define TF Hub paths to the BERT encoder and its preprocessor
bert_model_path ="/scratch/satyendrac.mnitjaipur/data/monika/embedding/small_bert_bert_en_uncased_L-2_H-256_A-4_2/"
bert_preprocess_path = "/scratch/satyendrac.mnitjaipur/data/monika/embedding/bert_en_uncased_preprocess_3/"

def make_bert_preprocessing_model(sentence_features, seq_length=128):
    """Returns Model mapping string features to BERT inputs.

  Args:
    sentence_features: A list with the names of string-valued features.
    seq_length: An integer that defines the sequence length of BERT inputs.

  Returns:
    A Keras Model that can be called on a list or dict of string Tensors
    (with the order or names, resp., given by sentence_features) and
    returns a dict of tensors for input to BERT.
  """

    input_segments = [
        tf.keras.layers.Input(shape=(), dtype=tf.string, name=ft)
        for ft in sentence_features
    ]

    # Tokenize the text to word pieces.
    bert_preprocess = hub.load(bert_preprocess_path)
    tokenizer = hub.KerasLayer(bert_preprocess.tokenize, name="tokenizer")
    segments = [tokenizer(s) for s in input_segments]

    # Optional: Trim segments in a smart way to fit seq_length.
    # Simple cases (like this example) can skip this step and let
    # the next step apply a default truncation to approximately equal lengths.
    truncated_segments = segments

    # Pack inputs. The details (start/end token ids, dict of output tensors)
    # are model-dependent, so this gets loaded from the SavedModel.
    packer = hub.KerasLayer(
        bert_preprocess.bert_pack_inputs,
        arguments=dict(seq_length=seq_length),
        name="packer",
    )
    model_inputs = packer(truncated_segments)
    return keras.Model(input_segments, model_inputs)


bert_preprocess_model = make_bert_preprocessing_model(["text_1"])
#keras.utils.plot_model(bert_preprocess_model, show_shapes=True, show_dtype=True)

idx = np.random.choice(len(train_df))
row = train_df.iloc[idx]
sample_text_1 = row["title"], 
print(f"Text 1: {sample_text_1}")

test_text = [np.array([sample_text_1])]
text_preprocessed = bert_preprocess_model(test_text)

print("Keys           : ", list(text_preprocessed.keys()))
print("Shape Word Ids : ", text_preprocessed["input_word_ids"].shape)
print("Word Ids       : ", text_preprocessed["input_word_ids"][0, :16])
print("Shape Mask     : ", text_preprocessed["input_mask"].shape)
print("Input Mask     : ", text_preprocessed["input_mask"][0, :16])
print("Shape Type Ids : ", text_preprocessed["input_type_ids"].shape)
print("Type Ids       : ", text_preprocessed["input_type_ids"][0, :16])

def dataframe_to_dataset(dataframe):
    columns = ["image_1_path",  "clean_title","label_idx"]
    dataframe = dataframe[columns].copy()
    labels = dataframe.pop("label_idx")
    ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
    ds = ds.shuffle(buffer_size=len(dataframe))
    return ds

resize = (128, 128)
bert_input_features = ["input_word_ids", "input_type_ids", "input_mask"]


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
    text_1 = tf.convert_to_tensor([text_1])
    output = bert_preprocess_model([text_1])
    output = {feature: tf.squeeze(output[feature]) for feature in bert_input_features}
    return output


def preprocess_text_and_image(sample):
    image_1 = preprocess_image(sample["image_1_path"])
    text = preprocess_text(sample["clean_title"])
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

#from tensorflow.keras.applications import EfficientNetB7
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.applications.inception_v3 import preprocess_input
def create_vision_encoder(
    num_projection_layers, projection_dims, dropout_rate, trainable=False
):
    # Load the pre-trained ResNet50V2 model to be used as the base encoder.
    #efficientnetb7 = EfficientNetB7(input_shape=(128,128,3),include_top=False, weights="imagenet",pooling='max' )
   
    # Set the trainability of the base encoder.
    #for layer in efficientnetb7.layers:
    #    layer.trainable = False
    inception = keras.applications.InceptionV3(input_shape=(128,128,3),include_top=False, weights="imagenet",pooling='max' )
    # Set the trainability of the base encoder.
    for layer in inception.layers:
        layer.trainable = False
    # Receive the images as inputs.
    image_1 = keras.Input(shape=(128, 128, 3), name="image_1")
   # image_2 = keras.Input(shape=(128, 128, 3), name="image_2")

    
    # Preprocess the input image.
    #preprocessed_1 = tf.keras.applications.efficientnet.preprocess_input(image_1)
  #  preprocessed_2 = tf.keras.applications.efficientnet.preprocess_input(image_2)
    preprocessed_1 = tf.keras.applications.inception_v3.preprocess_input(image_1)
    embeddings_1 = inception(preprocessed_1)
    # Generate the embeddings for the images using the resnet_v2 model
    # concatenate them.
    #embeddings_1 = efficientnetb7(preprocessed_1)
   # embeddings_2 = efficientnetb7(preprocessed_2)
    embeddings = keras.layers.Concatenate()([embeddings_1])

    # Project the embeddings produced by the model.
    outputs = project_embeddings(
        embeddings, num_projection_layers, projection_dims, dropout_rate
    )
    # Create the vision encoder model.
    return keras.Model([image_1], outputs, name="vision_encoder")

def create_text_encoder(
    num_projection_layers, projection_dims, dropout_rate, trainable=False
):
    # Load the pre-trained BERT model to be used as the base encoder.
    bert = hub.KerasLayer(bert_model_path, name="bert",)
    # Set the trainability of the base encoder.
    bert.trainable = trainable

    # Receive the text as inputs.
    bert_input_features = ["input_type_ids", "input_mask", "input_word_ids"]
    inputs = {
        feature: keras.Input(shape=(128,), dtype=tf.int32, name=feature)
        for feature in bert_input_features
    }

    # Generate embeddings for the preprocessed text using the BERT model.
    embeddings = bert(inputs)["pooled_output"]

    # Project the embeddings produced by the model.
    outputs = project_embeddings(
        embeddings, num_projection_layers, projection_dims, dropout_rate
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
    bert_input_features = ["input_type_ids", "input_mask", "input_word_ids"]
    text_inputs = {
        feature: keras.Input(shape=(128,), dtype=tf.int32, name=feature)
        for feature in bert_input_features
    }

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

text_inputs = {
        feature: keras.Input(shape=(128,), dtype=tf.int32, name=feature)
        for feature in bert_input_features
    }
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
#fit model
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

label_map = {"fake": 0, "real": 1}

print(classification_report(true_categories, predicted_categories, target_names=label_map, digits=4))

