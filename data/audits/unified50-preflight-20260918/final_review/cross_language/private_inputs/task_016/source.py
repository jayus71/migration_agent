=== cell 0: markdown ===
# Implementation of Multilayer Perceptron from Scratch

:label:`sec_mlp_scratch`


Now that we have characterized 
multilayer perceptrons (MLPs) mathematically, 
let us try to implement one ourselves.

=== cell 1: code ===
%load ../utils/djl-imports
%load ../utils/plot-utils
%load ../utils/DataPoints.java
%load ../utils/Training.java
%load ../utils/Accumulator.java

=== cell 2: code ===
import ai.djl.basicdataset.cv.classification.*;
import org.apache.commons.lang3.ArrayUtils;

=== cell 3: markdown ===
To compare against our previous results
achieved with (linear) softmax regression
(:numref:`sec_softmax_scratch`),
we will continue work with 
the Fashion-MNIST image classification dataset 
(:numref:`sec_fashion_mnist`).

=== cell 4: code ===
int batchSize = 256;

FashionMnist trainIter = FashionMnist.builder()
        .optUsage(Dataset.Usage.TRAIN)
        .setSampling(batchSize, true)
        .optLimit(Long.getLong("DATASET_LIMIT", Long.MAX_VALUE))
        .build();


FashionMnist testIter = FashionMnist.builder()
        .optUsage(Dataset.Usage.TEST)
        .setSampling(batchSize, true)
        .optLimit(Long.getLong("DATASET_LIMIT", Long.MAX_VALUE))
        .build();
                            
trainIter.prepare();
testIter.prepare();

=== cell 5: markdown ===
## Initializing Model Parameters

Recall that Fashion-MNIST contains $10$ classes,
and that each image consists of a $28 \times 28 = 784$
grid of (black and white) pixel values.
Again, we will disregard the spatial structure
among the pixels (for now),
so we can think of this as simply a classification dataset
with $784$ input features and $10$ classes.
To begin, we will implement an MLP
with one hidden layer and $256$ hidden units.
Note that we can regard both of these quantities
as *hyperparameters* and ought in general
to set them based on performance on validation data.
Typically, we choose layer widths in powers of $2$,
which tend to be computationally efficient because
of how memory is alotted and addressed in hardware.

Again, we will represent our parameters with several `NDArray`s.
Note that *for every layer*, we must keep track of
one weight matrix and one bias vector.
As always, we call `attachGradient()` to allocate memory
for the gradients (of the loss) with respect to these parameters.

=== cell 6: code ===
int numInputs = 784;
int numOutputs = 10;
int numHiddens = 256;

NDManager manager = NDManager.newBaseManager();

NDArray W1 = manager.randomNormal(
                        0, 0.01f, new Shape(numInputs, numHiddens), DataType.FLOAT32);
NDArray b1 = manager.zeros(new Shape(numHiddens));
NDArray W2 = manager.randomNormal(
                        0, 0.01f, new Shape(numHiddens, numOutputs), DataType.FLOAT32);
NDArray b2 = manager.zeros(new Shape(numOutputs));

NDList params = new NDList(W1, b1, W2, b2);

for (NDArray param : params) {
    param.setRequiresGradient(true);
}

=== cell 7: markdown ===
## Activation Function

To make sure we know how everything works,
we will implement the ReLU activation ourselves
using the `maximum` function rather than 
invoking `Activation.relu` directly.

=== cell 8: code ===
public NDArray relu(NDArray X){
    return X.maximum(0f);
}

=== cell 9: markdown ===
## The model

Because we are disregarding spatial structure, 
we `reshape` each 2D image into 
a flat vector of length  `numInputs`.
Finally, we implement our model 
with just a few lines of code.

=== cell 10: code ===
public NDArray net(NDArray X) {
    X = X.reshape(new Shape(-1, numInputs));
    NDArray H = relu(X.dot(W1).add(b1));
    return H.dot(W2).add(b2);
}

=== cell 11: markdown ===
## The Loss Function

To ensure numerical stability,
and because we already implemented
the softmax function from scratch
(:numref:`sec_softmax_scratch`),
we leverage Gluon's integrated function
for calculating the softmax and cross-entropy loss.
Recall our earlier discussion of these intricacies 
(:numref:`sec_mlp`).
We encourage the interested reader 
to examine the source code for `Loss.SoftmaxCrossEntropyLoss`
to deepen their knowledge of implementation details.

=== cell 12: code ===
Loss loss = Loss.softmaxCrossEntropyLoss();

=== cell 13: markdown ===
## Training

Fortunately, the training loop for MLPs
is exactly the same as for softmax regression.

We run the training like how we did in Chapter 3, 
(see :numref:`sec_softmax_scratch`),
setting the number of epochs to $10$ 
and the learning rate to $0.5$.

=== cell 14: code ===
int numEpochs = Integer.getInteger("MAX_EPOCH", 10);
float lr = 0.5f;

double[] trainLoss;
double[] testAccuracy;
double[] epochCount;
double[] trainAccuracy;

trainLoss = new double[numEpochs];
trainAccuracy = new double[numEpochs];
testAccuracy = new double[numEpochs];
epochCount = new double[numEpochs];

=== cell 15: code ===
float epochLoss = 0f;
float accuracyVal = 0f;

for (int epoch = 1; epoch <= numEpochs; epoch++) {
    System.out.print("Running epoch " + epoch + "...... ");
    // Iterate over dataset
    for (Batch batch : trainIter.getData(manager)) {

        NDArray X = batch.getData().head();
        NDArray y = batch.getLabels().head();

        try(GradientCollector gc = Engine.getInstance().newGradientCollector()) {
            NDArray yHat = net(X); // net function call

            NDArray lossValue = loss.evaluate(new NDList(y), new NDList(yHat));
            NDArray l = lossValue.mul(batchSize);

            accuracyVal += Training.accuracy(yHat, y);
            epochLoss += l.sum().getFloat();

            gc.backward(l); // gradient calculation
        }

        batch.close();
        Training.sgd(params, lr, batchSize); // updater
    }

    trainLoss[epoch-1] = epochLoss/trainIter.size();
    trainAccuracy[epoch-1] = accuracyVal/trainIter.size();

    epochLoss = 0f;
    accuracyVal = 0f;    
    // testing now
    for (Batch batch : testIter.getData(manager)) {

        NDArray X = batch.getData().head();
        NDArray y = batch.getLabels().head();

        NDArray yHat = net(X); // net function call
        accuracyVal += Training.accuracy(yHat, y);
    }

    testAccuracy[epoch-1] = accuracyVal/testIter.size();
    epochCount[epoch-1] = epoch;
    accuracyVal = 0f;
    System.out.println("Finished epoch " + epoch);
}

System.out.println("Finished training!");

=== cell 16: code ===
String[] lossLabel = new String[trainLoss.length + testAccuracy.length + trainAccuracy.length];

Arrays.fill(lossLabel, 0, trainLoss.length, "train loss");
Arrays.fill(lossLabel, trainAccuracy.length, trainLoss.length + trainAccuracy.length, "train acc");
Arrays.fill(lossLabel, trainLoss.length + trainAccuracy.length,
                trainLoss.length + testAccuracy.length + trainAccuracy.length, "test acc");

Table data = Table.create("Data").addColumns(
    DoubleColumn.create("epochCount", ArrayUtils.addAll(epochCount, ArrayUtils.addAll(epochCount, epochCount))),
    DoubleColumn.create("loss", ArrayUtils.addAll(trainLoss, ArrayUtils.addAll(trainAccuracy, testAccuracy))),
    StringColumn.create("lossLabel", lossLabel)
);

render(LinePlot.create("", data, "epochCount", "loss", "lossLabel"), "text/html");

=== cell 17: markdown ===
## Summary

We saw that implementing a simple MLP is easy, 
even when done manually.
That said, with a large number of layers, 
this can still get messy 
(e.g., naming and keeping track of our model's parameters, etc).

## Exercises

1. Change the value of the hyperparameter `numHiddens` and see how this hyperparameter influences your results. Determine the best value of this hyperparameter, keeping all others constant.
1. Try adding an additional hidden layer to see how it affects the results.
1. How does changing the learning rate alter your results? Fixing the model architecture and other hyperparameters (including number of epochs), what learning rate gives you the best results? 
1. What is the best result you can get by optimizing over all the parameters (learning rate, iterations, number of hidden layers, number of hidden units per layer) jointly? 
1. Describe why it is much more challenging to deal with multiple hyperparameters. 
1. What is the smartest strategy you can think of for structuring a search over multiple hyperparameters?

