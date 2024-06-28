# -*- coding: utf-8 -*-
"""dataset_validation.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Q7TrHfNIILFPaSKEsxCJtDimenC1VC-_
"""

random_seed = 100

# !pip install tensorflow-addons

# keras imports for the dataset and building our neural network
import tensorflow as tf
# import tensorflow_addons as tfa
from tensorflow import keras
from tensorflow.keras import layers

import numpy as np
import sklearn.metrics
import pandas as pd
import matplotlib.pyplot as plt
import inspect
from tqdm import tqdm
from keras.models import Sequential, Model,load_model
from keras.layers import Dense, Dropout, Conv2D, MaxPool2D, Flatten, Conv2DTranspose, ReLU
from keras.preprocessing.image import ImageDataGenerator
from keras import optimizers
import keras
from sklearn.metrics import confusion_matrix,classification_report,accuracy_score
import seaborn as sns
from tensorflow.keras import optimizers
from tensorflow.python.ops.numpy_ops import np_config

#saliency
! pip install tf-keras-vis tensorflow

from tensorflow.keras import backend as K

from mlxtend.evaluate import mcnemar
np_config.enable_numpy_behavior()

from google.colab import drive
drive.mount('/content/drive')

# loading the dataset
'''The paths for the data folders are not updated to match the data in this folder, the code won't run'''
batch_size=16
img_size = (224, 224)
img_shape = img_size + (3,)
print(img_shape)

directory = "/content/drive/MyDrive/Pap ML Project For Paper 2 (Shared Drive)/round 1"
train_ds = tf.keras.utils.image_dataset_from_directory(
    directory, labels='inferred', label_mode='int',
    class_names=None, color_mode='rgb', batch_size=batch_size, image_size=img_size,
    shuffle=True, seed=random_seed, validation_split=0.2, subset="training",
    interpolation='bilinear', follow_links=False,
    crop_to_aspect_ratio=False)

test_ds = tf.keras.utils.image_dataset_from_directory(
    directory, labels='inferred', label_mode='int',
    class_names=None, color_mode='rgb', batch_size=batch_size, image_size=img_size,
    shuffle=True, seed=random_seed, validation_split=0.2, subset="validation",
    interpolation='bilinear', follow_links=False,
    crop_to_aspect_ratio=False)

class_names = train_ds.class_names
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)
print(class_names)

tr_imgs = []
tr_labels = []

for element in train_ds.as_numpy_iterator():
  images, labels = element
  tr_imgs.append(images)
  tr_labels.append(labels)

tr_imgs = np.vstack(tr_imgs)
tr_labels = np.hstack(tr_labels)


t_imgs = []
t_labels = []

for element in test_ds.as_numpy_iterator():
  images, labels = element
  t_imgs.append(images)
  t_labels.append(labels)

t_imgs = np.vstack(t_imgs)
t_labels = np.hstack(t_labels)

"""### Train Test Split"""

from sklearn.model_selection import train_test_split
X_train, X_val, y_train, y_val = train_test_split(tr_imgs, tr_labels, test_size=0.25, random_state=random_seed, stratify=tr_labels)

"""### Augmentation"""

def augment(img, label):
  data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical", seed=random_seed),
    layers.RandomRotation(0.2, seed=random_seed),
  ])
  return data_augmentation(img), label

aug = list(map(augment, X_train, y_train))

for img, label in aug:
  X_train = np.append(X_train, np.expand_dims(img, axis=0), axis=0)
  y_train = np.append(y_train, label)

X_train.shape

def PlotPerformance(test_labels, test_pred, labels):
  cm=confusion_matrix(test_labels,test_pred)
  cr=classification_report(test_labels, test_pred)
  class_report=classification_report(test_labels, test_pred, target_names=labels, output_dict=True)
  ax= plt.subplot()
  sns.heatmap(cm, annot=True,ax=ax, fmt='d')
  ax.set_title('Confusion Matrix')
  ax.set_xlabel('Predicted labels')
  ax.set_ylabel('Actual labels')
  ax.xaxis.set_ticklabels(labels)
  ax.yaxis.set_ticklabels(labels)
  plt.show()
  ax= plt.subplot()
  sns.heatmap(pd.DataFrame(class_report).iloc[:-1, :].T,
              annot=True,ax=ax)
  ax.set_title('Classification Report')
  plt.show()
  return cm

"""## ML Models"""

tr_img_vec = []
for img in tr_imgs:
  tr_img_vec.append(img.flatten())
tr_img_vec = np.array(tr_img_vec) / 255.0

test_img_vec = []
for img in t_imgs:
  test_img_vec.append(img.flatten())
test_img_vec = np.array(test_img_vec) / 255.0

# from sklearn.preprocessing import StandardScaler
# ss = StandardScaler().fit(tr_img_vec)
# tr_img_vec = ss.transform(tr_img_vec)
# test_img_vec = ss.transform(test_img_vec)

from sklearn.decomposition import PCA
pca = PCA(n_components=80)
ml_train = pca.fit_transform(tr_img_vec)
ml_test = pca.transform(test_img_vec)

"""### SVC"""

from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

parameters = {'degree': range(3, 10), 'C':np.arange(0.5, 2, 0.1)}

# svc = SVC(C=1.4, probability=True).fit(ml_train, tr_labels)
# svc.score(ml_test, t_labels)
svc = SVC(probability=True)
clf = GridSearchCV(svc, parameters).fit(ml_train, tr_labels)
# probs = clf.predict_proba(ml_test)
clf.score(ml_test, t_labels)

y_pred_probs = clf.predict_proba(ml_test)

from sklearn.metrics import roc_curve, auc, RocCurveDisplay

fig, ax = plt.subplots()
colors = ['r', 'g', 'b']
for i in range(3):
  fpr, tpr, thresholds = roc_curve(t_labels, y_pred_probs[:, i], pos_label=i)
  roc_auc = auc(fpr, tpr)
  display = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name=class_names[i])
  display.plot(ax=ax, color=colors[i])

y_pred = clf.predict(ml_test)
PlotPerformance(t_labels, y_pred, class_names)

"""### Random Forest"""

from sklearn.ensemble import RandomForestClassifier

# Initialize the RandomForestClassifier
rf = RandomForestClassifier(n_estimators=100, random_state=random_seed).fit(ml_train, tr_labels)
rf.score(ml_test, t_labels)

from sklearn.metrics import roc_curve, auc, RocCurveDisplay

probs = rf.predict_proba(ml_test)
fig, ax = plt.subplots()
colors = ['r', 'g', 'b']
for i in range(3):
  fpr, tpr, thresholds = roc_curve(t_labels, probs[:, i], pos_label=i)
  roc_auc = auc(fpr, tpr)
  display = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name=class_names[i])
  display.plot(ax=ax, color=colors[i])

y_pred = rf.predict(ml_test)
PlotPerformance(t_labels, y_pred, class_names)

"""### DL Models"""

from tensorflow.keras import regularizers
model = tf.keras.models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3), kernel_regularizer=regularizers.l2(0.001)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu', kernel_regularizer=regularizers.l2(0.001)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu', kernel_regularizer=regularizers.l2(0.001)),
    layers.Flatten(),
    layers.Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
    layers.Dense(3, activation='softmax')
])

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'],
              run_eagerly=True)

y_train_ohe = tf.keras.utils.to_categorical(y_train, num_classes=3)
y_val_ohe = tf.keras.utils.to_categorical(y_val, num_classes=3)

from tensorflow.keras.applications.vgg19 import preprocess_input, VGG19
from tensorflow.keras.callbacks import ModelCheckpoint

vgg_train = preprocess_input(X_train)
vgg_val = preprocess_input(X_val)
vgg_test = preprocess_input(t_imgs)

vgg = tf.keras.applications.vgg19.VGG19(
    include_top=True,
    weights=None,
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=3,
    classifier_activation='softmax'
)
checkpoint_callback = ModelCheckpoint(
    filepath='/content/drive/MyDrive/best_vgg.h5',  # Path where the model will be saved
    monitor='val_accuracy',  # Monitor the validation loss
    save_best_only=True,  # Save only the best model
    mode='max',  # The model is considered better when the validation loss is minimized
    verbose=1  # Print a message when saving the model
)

vgg.compile(optimizer='sgd', loss=tf.keras.losses.SparseCategoricalCrossentropy(), metrics=['accuracy'], run_eagerly=True)
vgg.fit(vgg_train, y_train, epochs=20, batch_size=16, validation_data=(vgg_val, y_val), callbacks=[checkpoint_callback])
y_pred = vgg.predict(vgg_test)
y_pred = np.argmax(y_pred, axis=1)
1 - np.count_nonzero(y_pred-t_labels)/len(y_pred)



from tensorflow.keras.models import load_model

v = load_model("/content/drive/MyDrive/best_vgg.h5")
y_pred_probs = v.predict(vgg_test)
y_pred = np.argmax(y_pred_probs, axis=1)
1 - np.count_nonzero(y_pred-t_labels)/len(y_pred)

from sklearn.metrics import roc_curve, auc, RocCurveDisplay

fig, ax = plt.subplots()
colors = ['r', 'g', 'b']
for i in range(3):
  fpr, tpr, thresholds = roc_curve(t_labels, y_pred_probs[:, i], pos_label=i)
  roc_auc = auc(fpr, tpr)
  display = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name=class_names[i])
  display.plot(ax=ax, color=colors[i])

PlotPerformance(t_labels, y_pred, class_names)

from tensorflow.keras.applications.resnet50 import preprocess_input as preprocess_input_res
from tensorflow.keras.applications.resnet50 import ResNet50

from tensorflow.keras.callbacks import ModelCheckpoint


res_train = preprocess_input_res(X_train)
res_val = preprocess_input_res(X_val)
res_test = preprocess_input_res(t_imgs)

res = ResNet50(
    include_top=True,
    weights=None,
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=3,
    classifier_activation='softmax'
)
checkpoint_callback = ModelCheckpoint(
    filepath='/content/drive/MyDrive/res50.h5',  # Path where the model will be saved
    monitor='val_accuracy',  # Monitor the validation loss
    save_best_only=True,  # Save only the best model
    mode='max',  # The model is considered better when the validation loss is minimized
    verbose=1  # Print a message when saving the model
)

res.compile(optimizer='sgd', loss=tf.keras.losses.SparseCategoricalCrossentropy(), metrics=['accuracy'], run_eagerly=True)
res.fit(res_train, y_train, epochs=20, batch_size=16, validation_data=(res_val, y_val), callbacks=[checkpoint_callback])
y_pred = res.predict(res_test)
y_pred = np.argmax(y_pred, axis=1)
1 - np.count_nonzero(y_pred-t_labels)/len(y_pred)

r = load_model("/content/drive/MyDrive/res50.h5")

from tensorflow.keras.models import load_model

r = load_model("/content/drive/MyDrive/res50.h5")
y_pred_probs = r.predict(res_test)
y_pred = np.argmax(y_pred_probs, axis=1)
1 - np.count_nonzero(y_pred-t_labels)/len(y_pred)

PlotPerformance(t_labels, y_pred, class_names)

from sklearn.metrics import roc_curve, auc, RocCurveDisplay

fig, ax = plt.subplots()
colors = ['r', 'g', 'b']
for i in range(3):
  fpr, tpr, thresholds = roc_curve(t_labels, y_pred_probs[:, i], pos_label=i)
  roc_auc = auc(fpr, tpr)
  display = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name=class_names[i])
  display.plot(ax=ax, color=colors[i])

from tf_keras_vis.utils.model_modifiers import ReplaceToLinear

replace2linear = ReplaceToLinear()

# Instead of using the ReplaceToLinear instance above,
# you can also define the function from scratch as follows:
def model_modifier_function(cloned_model):
    cloned_model.layers[-1].activation = tf.keras.activations.linear

from tf_keras_vis.utils.scores import CategoricalScore

# 1 is the imagenet index corresponding to Goldfish, 294 to Bear and 413 to Assault Rifle.
score = CategoricalScore([0, 1, 2])

img1 = t_imgs[np.where(t_labels==0)[0][1]].copy()
print(t_imgs[np.where(t_labels==0)[0][1]][0][0])
print(img1[0][0])
img2 = t_imgs[np.where(t_labels==1)[0][1]].copy()
img3 = t_imgs[np.where(t_labels==2)[0][1]].copy()
pp_img1 = preprocess_input_res(img1.copy())
print(img1[0][0])
pp_img2 = preprocess_input_res(img2.copy())
pp_img3 = preprocess_input_res(img3.copy())
images = np.asarray([np.array(img1), np.array(img2), np.array(img3)])
pp_images = np.asarray([np.array(pp_img1), np.array(pp_img2), np.array(pp_img3)])

f, ax = plt.subplots(nrows=1, ncols=3, figsize=(9, 3))
for i, title in enumerate(class_names):
    ax[i].set_title(title, fontsize=16)
    ax[i].imshow(images[i] / 255.0)
    ax[i].axis('off')
plt.tight_layout()
plt.show()

# Commented out IPython magic to ensure Python compatibility.
# %%time
# from tf_keras_vis.saliency import Saliency
# 
# # Generate saliency map with smoothing that reduce noise by adding noise
# 
# saliency = Saliency(r,
#                     model_modifier=replace2linear,
#                     clone=True)
# saliency_map = saliency(score,
#                         images/255.0,
#                         smooth_samples=20, # The number of calculating gradients iterations.
#                         smooth_noise=0.20) # noise spread level.
# 
# ## Since v0.6.0, calling `normalize()` is NOT necessary.
# # saliency_map = normalize(saliency_map)
# 
# # Render
# f, ax = plt.subplots(nrows=1, ncols=3, figsize=(9, 3))
# for i, title in enumerate(class_names):
#     ax[i].set_title(title, fontsize=14)
#     ax[i].imshow(saliency_map[i], cmap='jet')
#     ax[i].axis('off')
# plt.tight_layout()
# # plt.savefig('images/smoothgrad.png')
# plt.show()
