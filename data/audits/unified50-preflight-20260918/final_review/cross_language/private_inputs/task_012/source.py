=== cell 0: markdown ===
# Linear Regression Implementation from Scratch
:label:`sec_linear_scratch`

Now that you understand the key ideas behind linear regression,
we can begin to work through a hands-on implementation in code.
In this section, we will implement the entire method from scratch,
including the data pipeline, the model,
the loss function, and the gradient descent optimizer.
While modern deep learning frameworks can automate nearly all of this work,
implementing things from scratch is the only
to make sure that you really know what you are doing.
Moreover, when it comes time to customize models,
defining our own layers, loss functions, etc.,
understanding how things work under the hood will prove handy.
In this section, we will rely only on `NDArray` and `GradientCollector`.
Afterwards, we will introduce a more compact implementation,
taking advantage of DJL's bells and whistles.
To start off, we import the few required packages.

=== cell 1: code ===
%load ../utils/djl-imports
%load ../utils/plot-utils

=== cell 2: markdown ===
## Generating the Dataset

To keep things simple, we will construct an artificial dataset
according to a linear model with additive noise.
Our task will be to recover this model's parameters
using the finite set of examples contained in our dataset.
We will keep the data low-dimensional so we can visualize it easily.
In the following code snippet, we generated a dataset 
containing $1000$ examples, each consisting of $2$ features
sampled from a standard normal distribution.
Thus our synthetic dataset will be an object
$\mathbf{X}\in \mathbb{R}^{1000 \times 2}$.

The true parameters generating our data will be 
$\mathbf{w} = [2, -3.4]^\top$ and $b = 4.2$
and our synthetic labels will be assigned according 
to the following linear model with noise term $\epsilon$:

$$\mathbf{y}= \mathbf{X} \mathbf{w} + b + \mathbf\epsilon.$$

You could think of $\epsilon$ as capturing potential 
measurement errors on the features and labels.
We will assume that the standard assumptions hold and thus
that $\epsilon$ obeys a normal distribution with mean of $0$.
To make our problem easy, we will set its standard deviation to $0.01$.
The following code generates our synthetic dataset:

=== cell 3: code ===
class DataPoints {
    private NDArray X, y;
    public DataPoints(NDArray X, NDArray y) {
        this.X = X;
        this.y = y;
    }
    
    public NDArray getX() {
        return X;
    }
    
    public NDArray getY() {
        return y;
    }
}

// Generate y = X w + b + noise
public DataPoints syntheticData(NDManager manager, NDArray w, float b, int numExamples) {
    NDArray X = manager.randomNormal(new Shape(numExamples, w.size()));
    NDArray y = X.matMul(w).add(b);
    // Add noise
    y = y.add(manager.randomNormal(0, 0.01f, y.getShape(), DataType.FLOAT32));
    return new DataPoints(X, y);
}

NDManager manager = NDManager.newBaseManager();

NDArray trueW = manager.create(new float[]{2, -3.4f});
float trueB = 4.2f;

DataPoints dp = syntheticData(manager, trueW, trueB, 1000);
NDArray features = dp.getX();
NDArray labels = dp.getY();

=== cell 4: markdown ===
Note that each row in `features` consists of a 2-dimensional data point 
and that each row in `labels` consists of a 1-dimensional target value (a scalar).

=== cell 5: code ===
System.out.printf("features: [%f, %f]\n", features.get(0).getFloat(0), features.get(0).getFloat(1));
System.out.println("label: " + labels.getFloat(0));

=== cell 6: markdown ===
By generating a scatter plot using the second feature `features[:, 1]` and `labels`, 
we can clearly observe the linear correlation between the two.

=== cell 7: code ===
float[] X = features.get(new NDIndex(":, 1")).toFloatArray();
float[] y = labels.toFloatArray();

Table data = Table.create("Data")
    .addColumns(
        FloatColumn.create("X", X),
        FloatColumn.create("y", y)
    );

ScatterPlot.create("Synthetic Data", data, "X", "y");

=== cell 8: markdown ===
## Reading the Dataset

Recall that training models consists of 
making multiple passes over the dataset, 
grabbing one minibatch of examples at a time,
and using them to update our model. 
We can use `ArrayDataset` to randomly sample
the data and access it in minibatches.

In the following code, we instantiate an `ArrayDataset`.
We then set parameters for `features`, `labels`, `batchSize`, 
and `sampling`. 

With `dataset.getData`, we can get minibatches of size `batchSize`,
each consisting of its features and labels.

=== cell 9: code ===
import ai.djl.training.dataset.ArrayDataset;
import ai.djl.training.dataset.Batch;

int batchSize = 10;

ArrayDataset dataset = new ArrayDataset.Builder()
                          .setData(features) // Set the Features
                          .optLabels(labels) // Set the Labels
                          .setSampling(batchSize, false) // set the batch size and random sampling to false
                          .build();

=== cell 10: markdown ===
In general, note that we want to use reasonably sized minibatches
to take advantage of the GPU hardware,
which excels at parallelizing operations.
Because each example can be fed through our models in parallel
and the gradient of the loss function for each example can also be taken in parallel,
GPUs allow us to process hundreds of examples in scarcely more time
than it might take to process just a single example.

To build some intuition, let us read and print
the first small batch of data examples.
The shape of the features in each minibatch tells us
both the minibatch size and the number of input features.
Likewise, our minibatch of labels will have a shape given by `batchSize`.

=== cell 11: code ===
Batch batch = dataset.getData(manager).iterator().next();
// Call head() to get the first NDArray
NDArray X = batch.getData().head();
NDArray y = batch.getLabels().head();
System.out.println(X);
System.out.println(y);
// Don't forget to close the batch!
batch.close();

=== cell 12: markdown ===
As we run the iterator, we obtain distinct minibatches 
successively until all the data has been exhausted (try this).
While the iterator implemented above is good for didactic purposes,
it is inefficient in ways that might get us in trouble on real problems.
For example, it requires that we load all data in memory
and that we perform lots of random memory access.
The built-in iterators implemented in DJL
are considerably more efficient and they can deal
both with data stored in file and data fed via a data stream.

## Initializing Model Parameters

Before we can begin optimizing our model's parameters by gradient descent,
we need to have some parameters in the first place.
In the following code, we initialize weights by sampling
random numbers from a normal distribution with mean 0
and a standard deviation of $0.01$, setting the bias $b$ to $0$.

=== cell 13: code ===
NDArray w = manager.randomNormal(0, 0.01f, new Shape(2, 1), DataType.FLOAT32);
NDArray b = manager.zeros(new Shape(1));
NDList params = new NDList(w, b);

=== cell 14: markdown ===
Now that we have initialized our parameters,
our next task is to update them until 
they fit our data sufficiently well.
Each update requires taking the gradient
(a multi-dimensional derivative)
of our loss function with respect to the parameters.
Given this gradient, we can update each parameter
in the direction that reduces the loss.

Since nobody wants to compute gradients explicitly
(this is tedious and error prone),
we use automatic differentiation to compute the gradient.
See :numref:`sec_gradcollector` for more details.
Recall from the autograd chapter
that in order for `GradientCollector` to know
that it should store a gradient for our parameters,
we need to invoke the `attachGradient()` function,
allocating memory to store the gradients that we plan to take.

=== cell 15: markdown ===
## Defining the Model

Next, we must define our model,
relating its inputs and parameters to its outputs.
Recall that to calculate the output of the linear model,
we simply take the matrix-vector dot product
of the examples $\mathbf{X}$ and the models weights $w$,
and add the offset $b$ to each example.
Note that below `X.dot(w)` is a vector and `b` is a scalar.
Recall that when we add a vector and a scalar,
the scalar is added to each component of the vector.

=== cell 16: code ===
// Saved in Training.java for later use
public NDArray linreg(NDArray X, NDArray w, NDArray b) {
    return X.dot(w).add(b);
}

=== cell 17: markdown ===
## Defining the Loss Function

Since updating our model requires taking 
the gradient of our loss function,
we ought to define the loss function first.
Here we will use the squared loss function
as described in the previous section.
In the implementation, we need to transform the true value `y` 
into the predicted value's shape `yHat`.
The result returned by the following function
will also be the same as the `yHat` shape.

=== cell 18: code ===
// Saved in Training.java for later use
public NDArray squaredLoss(NDArray yHat, NDArray y) {
    return (yHat.sub(y.reshape(yHat.getShape()))).mul 
        ((yHat.sub(y.reshape(yHat.getShape())))).div(2);
}

=== cell 19: markdown ===
## Defining the Optimization Algorithm

As we discussed in the previous section,
linear regression has a closed-form solution.
However, this is not a book about linear regression,
it is a book about deep learning.
Since none of the other models that this book introduces
can be solved analytically, we will take this opportunity to introduce your first working example of stochastic gradient descent (SGD).


At each step, using one batch randomly drawn from our dataset,
we will estimate the gradient of the loss with respect to our parameters.
Next, we will update our parameters (a small amount)
in the direction that reduces the loss.
Recall from :numref:`sec_gradcollector` that after we call `backward()`, 
each parameter (`param`) will have its gradient stored in `param.getGradient()`.
The following code applies the SGD update,
given a set of parameters, a learning rate, and a batch size.
The size of the update step is determined by the learning rate `lr`.
Because our loss is calculated as a sum over the batch of examples,
we normalize our step size by the batch size (`batchSize`),
so that the magnitude of a typical step size
does not depend heavily on our choice of the batch size.

=== cell 20: code ===
// Saved in Training.java for later use
public static void sgd(NDList params, float lr, int batchSize) {
    for (int i = 0; i < params.size(); i++) {
        NDArray param = params.get(i);
        // Update param
        // param = param - param.gradient * lr / batchSize
        param.subi(param.getGradient().mul(lr).div(batchSize));
    }
}

=== cell 21: markdown ===
## Training

Now that we have all of the parts in place,
we are ready to implement the main training loop.
It is crucial that you understand this code
because you will see nearly identical training loops
over and over again throughout your career in deep learning.

In each iteration, we will grab minibatches of training dataset,
first passing them through our model to obtain a set of predictions.
After calculating the loss, we call the `backward()` function
to initiate the backwards pass through the network, 
storing the gradients with respect to each parameter in its corresponding `gradient` attribute. Technically since `NDArray` is an interface for each engine's implementation, there is no standard `gradient` attribute, but we can safely assume that we can access them however they are stored with `getGradient()`.
Finally, we will call the optimization algorithm `sgd`
to update the model parameters.
Since we previously set the batch size `batchSize` to $10$,
the loss shape `l` for each minibatch is ($10$, $1$).

In summary, we will execute the following loop:

* Initialize parameters $(\mathbf{w}, b)$
* Repeat until done
    * Compute gradient $\mathbf{g} \leftarrow \partial_{(\mathbf{w},b)} \frac{1}{\mathcal{B}} \sum_{i \in \mathcal{B}} l(\mathbf{x}^i, y^i, \mathbf{w}, b)$
    * Update parameters $(\mathbf{w}, b) \leftarrow (\mathbf{w}, b) - \eta \mathbf{g}$

In the code below, `l` is a vector of the losses
for each example in the minibatch.

In each epoch (a pass through the data),
we will iterate through the entire dataset
(using the `dataset.getData()` function) once
passing through every examples in the training dataset
(assuming the number of examples is divisible by the batch size).
The number of epochs `numEpochs` and the learning rate `lr` are both hyper-parameters, 
which we set here to $3$ and $0.03$, respectively. 
Unfortunately, setting hyper-parameters is tricky
and requires some adjustment by trial and error.
We elide these details for now but revise them
later in
:numref:`chap_optimization`.

Note: We can replace `linreg` and `squaredLoss` with any net or loss function respectively
and still keep the same training structure shown here.

=== cell 22: code ===
float lr = 0.03f;  // Learning Rate
int numEpochs = 3;  // Number of Iterations

// Attach Gradients
for (NDArray param : params) {
    param.setRequiresGradient(true);
}

for (int epoch = 0; epoch < numEpochs; epoch++) {
    // Assuming the number of examples can be divided by the batch size, all
    // the examples in the training dataset are used once in one epoch
    // iteration. The features and tags of minibatch examples are given by X
    // and y respectively.
    for (Batch batch : dataset.getData(manager)) {
        NDArray X = batch.getData().head();
        NDArray y = batch.getLabels().head();
        
        try (GradientCollector gc = Engine.getInstance().newGradientCollector()) {
            // Clear the gradients from the previous batch
            gc.zeroGradients();
            // Minibatch loss in X and y
            NDArray l = squaredLoss(linreg(X, params.get(0), params.get(1)), y);
            gc.backward(l);  // Compute gradient on l with respect to w and b
        }
        sgd(params, lr, batchSize);  // Update parameters using their gradient
        
        batch.close();
    }
    NDArray trainL = squaredLoss(linreg(features, params.get(0), params.get(1)), labels);
    System.out.printf("epoch %d, loss %f\n", epoch + 1, trainL.mean().getFloat());
}

=== cell 23: markdown ===
In this case, because we synthesized the data ourselves,
we know precisely what the true parameters are. 
Thus, we can evaluate our success in training 
by comparing the true parameters
with those that we learned through our training loop. 
Indeed they turn out to be very close to each other.

=== cell 24: code ===
float[] w = trueW.sub(params.get(0).reshape(trueW.getShape())).toFloatArray();
System.out.println(String.format("Error in estimating w: [%f, %f]", w[0], w[1]));
System.out.println(String.format("Error in estimating b: %f", trueB - params.get(1).getFloat()));

=== cell 25: markdown ===
Note that we should not take it for granted
that we are able to recover the parameters accurately.
This only happens for a special category problems:
strongly convex optimization problems with "enough" data to ensure
that the noisy samples allow us to recover the underlying dependency.
In most cases this is *not* the case.
In fact, the parameters of a deep network 
are rarely the same (or even close) between two different runs, 
unless all conditions are identical,
including the order in which the data is traversed.
However, in machine learning, we are typically less concerned
with recovering true underlying parameters,
and more concerned with parameters that lead to accurate prediction.
Fortunately, even on difficult optimization problems,
stochastic gradient descent can often find remarkably good solutions,
owing partly to the fact that, for deep networks,
there exist many configurations of the parameters 
that lead to accurate prediction.

## Summary

We saw how a deep network can be implemented
and optimized from scratch, using just `NDArray` and `GradientCollector`,
without any need for defining layers, fancy optimizers, etc.
This only scratches the surface of what is possible.
In the following sections, we will describe additional models
based on the concepts that we have just introduced
and learn how to implement them more concisely.

## Exercises

1. What would happen if we were to initialize the weights $\mathbf{w} = 0$. Would the algorithm still work?
1. Assume that you are [Georg Simon Ohm](https://en.wikipedia.org/wiki/Georg_Ohm) trying to come up with a model between voltage and current. Can you use `GradientCollector` to learn the parameters of your model.
1. Can you use [Planck's Law](https://en.wikipedia.org/wiki/Planck%27s_law) to determine the temperature of an object using spectral energy density?
1. What are the problems you might encounter if you wanted to extend `GradientCollector` to second derivatives? How would you fix them?
1.  Why is the `reshape()` function needed in the `squaredLoss()` function?
1. Experiment using different learning rates to find out how fast the loss function value drops.
1. If the number of examples cannot be divided by the batch size, what happens to the `dataset.getData()` function's behavior?
