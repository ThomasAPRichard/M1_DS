import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

input_d = 3
hidden_d = 8

#Build one feed forward neural network with one hidden layer with dimension ``hidden_d`` with activation function ``relu``
model = Sequential()
model.add(Input((input_d,)))
model.add(Dense(hidden_d, input_dim=input_d, activation='relu'))
model.add(Dense(1, activation='linear'))

# Set the optimizer as ``adam`` and the loss function as the ``mean_squared_error``
model.compile(optimizer='adam', loss='mean_squared_error')
model.summary()

# Train the model using ``model.fit``
dataset = np.loadtxt('./chennai_reservoir_levels.csv', delimiter='|', skiprows=1, usecols=(1,2,3,4))
np.random.shuffle(dataset)
X = dataset[:, 0:3]
y = dataset[:, 3]

X_train, X_test, y_train, y_test = train_test_split(X, y)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)
y_train = scaler.fit_transform(y_train.reshape(-1, 1))
y_test = scaler.transform(y_test.reshape(-1, 1))

result = model.fit(X_train, y_train, epochs=10, batch_size=5, verbose=1, shuffle=True)
plt.xlabel("Epochs")
plt.ylabel("MSE") 
plt.plot(result.history["loss"])
plt.show()

# Display predictions on the train dataset
y_pred_train = model.predict(X_train)
sns.stripplot(data=y_train, alpha=.4, label="ground truth")
sns.stripplot(data=y_pred_train, alpha=.4, label="predictions")
plt.ylabel("Water level sur train")
plt.legend()
plt.show()

# Display predictions on the test dataset
y_pred = model.predict(X_test)
plt.scatter(y_test, y_pred)
plt.xlabel("Ground truth")
plt.ylabel("Predictions")
plt.ylabel("Water level sur test")
plt.legend()
plt.show()

# Analyze the impact of the number of layers.
