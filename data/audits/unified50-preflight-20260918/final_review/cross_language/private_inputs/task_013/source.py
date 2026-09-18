=== cell 0: markdown ===
# Concise Implementation of Softmax Regression
:label:`sec_softmax_djl`

Just as DJL made it much easier
to implement linear regression in :numref:`sec_linear_djl`,
we will find it similarly (or possibly more)
convenient for implementing classification models.
Again, we begin with our import ritual.

=== cell 1: code ===
%load ../utils/djl-imports

import ai.djl.basicdataset.cv.classification.*;
import ai.djl.metric.*;

=== cell 2: markdown ===
Let us stick with the Fashion-MNIST dataset 
and keep the batch size at $256$ as in the last section.

=== cell 3: code ===
int batchSize = 256;
boolean randomShuffle = true;

// Get Training and Validation Datasets
FashionMnist trainingSet = FashionMnist.builder()
        .optUsage(Dataset.Usage.TRAIN)
        .setSampling(batchSize, randomShuffle)
        .optLimit(Long.getLong("DATASET_LIMIT", Long.MAX_VALUE))
        .build();


FashionMnist validationSet = FashionMnist.builder()
        .optUsage(Dataset.Usage.TEST)
        .setSampling(batchSize, false)
        .optLimit(Long.getLong("DATASET_LIMIT", Long.MAX_VALUE))
        .build();

=== cell 4: markdown ===
## Initializing Model Parameters

As mentioned in :numref:`sec_softmax`,
the output layer of softmax regression 
is a fully-connected (`Dense`) layer.
Therefore, to implement our model,
we just need to add one `Dense` layer 
with 10 outputs to our `Sequential`.
Again, here, the `Sequential` is not really necessary,
but we might as well form the habit since it will be ubiquitous
when implementing deep models.

=== cell 5: code ===
public class ActivationFunction {
    public static NDList softmax(NDList arrays) {
        return new NDList(arrays.singletonOrThrow().logSoftmax(1));
    }
}

=== cell 6: code ===
NDManager manager = NDManager.newBaseManager();

Model model = Model.newInstance("softmax-regression");

SequentialBlock net = new SequentialBlock();
net.add(Blocks.batchFlattenBlock(28 * 28)); // flatten input
net.add(Linear.builder().setUnits(10).build()); // set 10 output channels

model.setBlock(net);

=== cell 7: markdown ===
## The Softmax

In the previous example, we calculated our model's output
and then ran this output through the cross-entropy loss.
Mathematically, that is a perfectly reasonable thing to do.
However, from a computational perspective, 
exponentiation can be a source of numerical stability issues
(as discussed  in :numref:`sec_naive_bayes`).
Recall that the softmax function calculates
$\hat y_j = \frac{e^{z_j}}{\sum_{i=1}^{n} e^{z_i}}$, 
where $\hat y_j$ is the $j^\mathrm{th}$ element of ``yHat`` 
and $z_j$ is the $j^\mathrm{th}$ element of the input
``yLinear`` variable, as computed by the softmax.

If some of the $z_i$ are very large (i.e., very positive),
then $e^{z_i}$ might be larger than the largest number
we can have for certain types of ``float`` (i.e., overflow).
This would make the denominator (and/or numerator) ``inf`` 
and we wind up encountering either $0$, ``inf``, or ``nan`` for $\hat y_j$.
In these situations we do not get a well-defined 
return value for ``crossEntropy()``.
One trick to get around this is to first subtract $\text{max}(z_i)$
from all $z_i$ before proceeding with the ``softmax`` calculation.
You can verify that this shifting of each $z_i$ by constant factor
does not change the return value of ``softmax()``.

After the subtraction and normalization step,
it might be possible that some $z_j$ have large negative values
and thus that the corresponding $e^{z_j}$ will take values close to zero.
These might be rounded to zero due to finite precision (i.e underflow),
making $\hat y_j$ zero and giving us ``-inf`` for $\text{log}(\hat y_j)$.
A few steps down the road in backpropagation,
we might find ourselves faced with a screenful 
of the dreaded not-a-number (``nan``) results.

Fortunately, we are saved by the fact that 
even though we are computing exponential functions, 
we ultimately intend to take their log 
(when calculating the cross-entropy loss).
By combining these two operators 
(``softmax`` and ``crossEntropy``) together,
we can escape the numerical stability issues
that might otherwise plague us during backpropagation.
As shown in the equation below, we avoided calculating $e^{z_j}$
and can use instead $z_j$ directly due to the canceling in $\log(\exp(\cdot))$.

$$
\begin{aligned}
\log{(\hat y_j)} & = \log\left( \frac{e^{z_j}}{\sum_{i=1}^{n} e^{z_i}}\right) \\
& = \log{(e^{z_j})}-\text{log}{\left( \sum_{i=1}^{n} e^{z_i} \right)} \\
& = z_j -\log{\left( \sum_{i=1}^{n} e^{z_i} \right)}.
\end{aligned}
$$

We will want to keep the conventional softmax function handy
in case we ever want to evaluate the probabilities output by our model.
But instead of passing softmax probabilities into our new loss function,
we will just pass the logits and compute the softmax and its log
all at once inside the softmaxCrossEntropy loss function,
which does smart things like the log-sum-exp trick ([see on Wikipedia](https://en.wikipedia.org/wiki/LogSumExp)).

=== cell 8: code ===
Loss loss = Loss.softmaxCrossEntropyLoss();

=== cell 9: markdown ===
## Optimization Algorithm

Here, we use minibatch stochastic gradient descent
with a learning rate of $0.1$ as the optimization algorithm.
Note that this is the same as we applied in the linear regression example
and it illustrates the general applicability of the optimizers.

=== cell 10: code ===
Tracker lrt = Tracker.fixed(0.1f);
Optimizer sgd = Optimizer.sgd().setLearningRateTracker(lrt).build();

=== cell 11: markdown ===
## Instantiate Configuration
Now we'll create a training configuration that
describes how we want to train our model.
We will then create a `trainer` to do the
training for us.

=== cell 12: code ===
DefaultTrainingConfig config = new DefaultTrainingConfig(loss)
    .optOptimizer(sgd) // Optimizer
    .optDevices(manager.getEngine().getDevices(1)) // single GPU
    .addEvaluator(new Accuracy()) // Model Accuracy
    .addTrainingListeners(TrainingListener.Defaults.logging()); // Logging

Trainer trainer = model.newTrainer(config);

=== cell 13: markdown ===
## Initializing Trainer
We initialize the trainer with input shape ($1$, $748$).

=== cell 14: code ===
trainer.initialize(new Shape(1, 28 * 28)); // Input Images are 28 x 28

=== cell 15: markdown ===
## Metrics
Now we tell DJL to record metrics! (Remember, DJL doesn't record metrics unless you tell it to!)

=== cell 16: code ===
Metrics metrics = new Metrics();
trainer.setMetrics(metrics);

=== cell 17: markdown ===
## Training

In :numref:`sec_linear_djl`, we train the model by explicitly calling `EasyTrain` to train each batch and then updating the parameters. We can actually instead call `EasyTrain`'s `fit()` function to do this for us in 1 line. It takes in a given number of epochs, a training set, and a validation set and, along with the training, will do the validation for us as well!

=== cell 18: code ===
int numEpochs = 3;

EasyTrain.fit(trainer, numEpochs, trainingSet, validationSet);
var result = trainer.getTrainingResult();

=== cell 19: markdown ===
As before, this algorithm converges to a solution
that achieves an accuracy of 83.7%,
albeit this time with fewer lines of code than before.
Note that in many cases, DJL takes additional precautions
beyond these most well-known tricks to ensure numerical stability,
saving us from even more pitfalls that we would encounter
if we tried to code all of our models from scratch in practice.

## Exercises

1. Try adjusting the hyper-parameters, such as batch size, epoch, and learning rate, to see what the results are.
1. Why might the test accuracy decrease again after a while? How could we fix this?