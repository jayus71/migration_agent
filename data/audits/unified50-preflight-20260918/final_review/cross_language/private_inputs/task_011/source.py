=== cell 0: markdown ===
# Concise Implementation of Linear Regression
:label:`sec_linear_djl`

Broad and intense interest in deep learning for the past several years
has inspired both companies, academics, and hobbyists
to develop a variety of mature open source frameworks
for automating the repetitive work of implementing
gradient-based learning algorithms.
In the previous section, we relied only on
(i) `NDArray` for data storage and linear algebra;
and (ii) `GradientCollector` for calculating derivatives.
In practice, because data iterators, loss functions, optimizers,
and neural network layers (and some whole architectures)
are so common, modern libraries implement these components for us as well.

In this section, we will show you how to implement
the linear regression model from :numref:`sec_linear_scratch`
concisely by using DJL.

## Generating the Dataset

To start, we will generate the same dataset as in the previous section.

=== cell 1: code ===
%load ../utils/djl-imports
%load ../utils/DataPoints.java
%load ../utils/Training.java

=== cell 2: code ===
NDManager manager = NDManager.newBaseManager();

NDArray trueW = manager.create(new float[]{2, -3.4f});
float trueB = 4.2f;

DataPoints dp = DataPoints.syntheticData(manager, trueW, trueB, 1000);
NDArray features = dp.getX();
NDArray labels = dp.getY();

=== cell 3: markdown ===
## Reading the Dataset

Just like in the last section,
we can call upon DJL's `dataset` package to read data.
The first step will be to instantiate an `ArrayDataset`.
Here, we set the `features` and `labels` as parameters.
We also specify a `batchSize`
and specify a Boolean value `shuffle` indicating whether or not
we want the `ArrayDataset` to randomly sample the data.

=== cell 4: code ===
// Saved in the utils file for later use
public ArrayDataset loadArray(NDArray features, NDArray labels, int batchSize, boolean shuffle) {
    return new ArrayDataset.Builder()
                  .setData(features) // set the features
                  .optLabels(labels) // set the labels
                  .setSampling(batchSize, shuffle) // set the batch size and random sampling
                  .build();
}

int batchSize = 10;
ArrayDataset dataset = loadArray(features, labels, batchSize, false);

=== cell 5: markdown ===
To verify that it is working, we can read and print
the first minibatch of instances.

=== cell 6: code ===
Batch batch = dataset.getData(manager).iterator().next();
NDArray X = batch.getData().head();
NDArray y = batch.getLabels().head();
System.out.println(X);
System.out.println(y);
batch.close();

=== cell 7: markdown ===
## Defining the Model

When we implemented linear regression from scratch
(in :numref:`sec_linear_scratch`),
we defined our model parameters explicitly
and coded up the calculations to produce output
using basic linear algebra operations.
You *should* know how to do this.
But once your models get more complex,
and once you have to do this nearly every day,
you will be glad for the assistance.
The situation is similar to coding up your own blog from scratch.
Doing it once or twice is rewarding and instructive,
but you would be a lousy web developer
if every time you needed a blog you spent a month
reinventing the wheel.

For standard operations, we can use DJL's predefined blocks,
which allow us to focus especially
on the layers used to construct the model
rather than having to focus on the implementation.
To define a linear model, we first import the `Model` class,
which defines a lot of useful methods to interact with our `model`.
We will first define a model variable `model`.
We will then instantiate a SequentialBlock variable `net`, which will refer to an instance of the `SequentialBlock` class. The `SequentialBlock` class defines a container for several layers that will be chained together. Given input data, a `SequentialBlock` passes it through the first layer, in turn passing the output as the second layer’s input and so forth. In the following example, our model consists of only one layer, so we do not really need `SequentialBlock`. But since nearly all of our future models will involve multiple layers, we will use it anyway just to familiarize you with the most standard workflow.

=== cell 8: markdown ===
Recall the architecture of a single-layer network as shown in :numref:`fig_singleneuron`.
The layer is said to be *fully-connected*
because each of its inputs are connected to each of its outputs
by means of a matrix-vector multiplication.
In DJL, we can use a `Linear` block to apply a linear transformation.
We simply set the number of outputs (in our case its set to 1) and choose
if we want to include a bias(yes).

![Linear regression is a single-layer neural network. ](https://resources.djl.ai/d2l-java/singleneuron.svg)
:label:`fig_singleneuron`

=== cell 9: code ===
Model model = Model.newInstance("lin-reg");

SequentialBlock net = new SequentialBlock();
Linear linearBlock = Linear.builder().optBias(true).setUnits(1).build();
net.add(linearBlock);

model.setBlock(net);

=== cell 10: markdown ===
## Defining the Loss Function

In DJL, the `Loss` class defines various loss functions.
We will use the imported class `Loss`.
In this example, we will use the DJL
implementation of squared loss (`L2Loss`).

$$
L2Loss = \sum_{i = 1}^{n}(y_i - \hat{y_i})^2
$$

L2 Loss or 'Mean Squared Error' is the sum of the squared
difference between the true `y` value and the predicted `y`
value.

=== cell 11: code ===
Loss l2loss = Loss.l2Loss();

=== cell 12: markdown ===
## Defining the Optimization Algorithm

Minibatch SGD and related variants
are standard tools for optimizing neural networks
and thus DJL supports SGD alongside a number of
variations on this algorithm through its `Optimizer` class.
When we instantiate the `Optimizer`,
we will specify the optimization algorithm we wish to use (`sgd`).
We can also manually set hyper-parameters.
SGD just requires `learningRate`,
here we set it to a fixed rate of 0.03.

=== cell 13: code ===
Tracker lrt = Tracker.fixed(0.03f);
Optimizer sgd = Optimizer.sgd().setLearningRateTracker(lrt).build();

=== cell 14: markdown ===
## Instantiate Configuration and Trainer
Now we'll create a training configuration that
describes how we want to train our model.
We will then initialize a `trainer` to do the
training for us.

=== cell 15: code ===
DefaultTrainingConfig config = new DefaultTrainingConfig(l2loss)
    .optOptimizer(sgd) // Optimizer (loss function)
    .optDevices(manager.getEngine().getDevices(1)) // single GPU
    .addTrainingListeners(TrainingListener.Defaults.logging()); // Logging

Trainer trainer = model.newTrainer(config);

=== cell 16: markdown ===
## Initializing Model Parameters

Before training our model, we need to initialize the model parameters,
such as the weights and biases in the linear regression model.
We simply call the `initialize` function with the shape of the model
we are training.

=== cell 17: code ===
// First axis is batch size - won't impact parameter initialization
// Second axis is the input size
trainer.initialize(new Shape(batchSize, 2));

=== cell 18: markdown ===
## Metrics
Normally, DJL doesn't record metrics unless explicitly told to
as recording metrics impacts the execution flow optimizations.
To record metrics, we must instantiate `metrics` from outside
the `trainer` object and then pass it in.

=== cell 19: code ===
Metrics metrics = new Metrics();
trainer.setMetrics(metrics);

=== cell 20: markdown ===
## Training

You might have noticed that expressing our model through DJL
requires comparatively few lines of code.
We did not have to individually allocate parameters,
define our loss function, or implement stochastic gradient descent.
Once we start working with much more complex models,
DJL's advantages will grow considerably.
However, once we have all the basic pieces in place,
the training loop itself is strikingly similar
to what we did when implementing everything from scratch.

To refresh your memory: for some number of epochs,
we will make a complete pass over the dataset (train_data),
iteratively grabbing one minibatch of inputs
and the corresponding ground-truth labels.
For each minibatch, we go through the following ritual:

* Generate predictions, calculate loss, and calculate gradients by calling `trainBatch(batch)` (forward pass and backward pass).
* Update the model parameters by invoking the `step` function.

`Logging` will automatically print the evaluators we are watching
during each epoch.

=== cell 21: code ===
int numEpochs = 3;

for (int epoch = 1; epoch <= numEpochs; epoch++) {
    System.out.printf("Epoch %d\n", epoch);
    // Iterate over dataset
    for (Batch batch : trainer.iterateDataset(dataset)) {
        // Update loss and evaulator
        EasyTrain.trainBatch(trainer, batch);
        
        // Update parameters
        trainer.step();
        
        batch.close();
    }
    // reset training and validation evaluators at end of epoch
    trainer.notifyListeners(listener -> listener.onEpoch(trainer));
}

=== cell 22: markdown ===
Below, we compare the model parameters learned by training on finite data
and the actual parameters that generated our dataset.
To access parameters with DJL,
we first access the layer that we need from `model`
and then access that layer's weight and bias through its parameter list
by calling `getParameters()`.
We then simply get each param with `valueAt()`.
Here, `valueAt(0)` and `valueAt(1)` returns the weights and bias respectively.
As in our from-scratch implementation,
note that our estimated parameters are
close to their ground truth counterparts.

=== cell 23: code ===
Block layer = model.getBlock();
ParameterList params = layer.getParameters();
NDArray wParam = params.valueAt(0).getArray();
NDArray bParam = params.valueAt(1).getArray();

float[] w = trueW.sub(wParam.reshape(trueW.getShape())).toFloatArray();
System.out.printf("Error in estimating w: [%f %f]\n", w[0], w[1]);
System.out.printf("Error in estimating b: %f\n", trueB - bParam.getFloat());

=== cell 24: markdown ===
## Saving Your Model
Now that you have trained your model, you probably want to save it
for future use. Additionally, you probably also want to add
metadata such as training accuracy and epochs trained.
You can do this easily. Simply point to a file location with `Paths.get`.
Metadata can be saved with the `setProperty` method.
Then call the `save` method on the model to save it!

=== cell 25: code ===
Path modelDir = Paths.get("../models/lin-reg");
Files.createDirectories(modelDir);

model.setProperty("Epoch", Integer.toString(numEpochs)); // save epochs trained as metadata

model.save(modelDir, "lin-reg");

model

=== cell 26: markdown ===
## Summary

* Using DJL, we can implement models much more succinctly.
* In DJL, the `training.dataset` package provides tools for data processing, the `nn` package defines a large number of neural network layers, and the `Loss` class defines many common loss functions.
* DJL's `training.initializer` package provides various methods for model parameter initialization.


## Exercises

1. Review the DJL documentation to see what loss functions and initialization methods are provided in the class `Loss` and `Trainer`. Replace the loss with L1 Loss.
1. How do you access the parameters during training?
