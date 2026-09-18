=== cell 0: markdown ===
# Concise Implementation of Recurrent Neural Networks
:label:`sec_rnn-concise`

While :numref:`sec_rnn_scratch` was instructive to see how RNNs are implemented,
this is not convenient or fast.
This section will show how to implement the same language model more efficiently
using functions provided by high-level APIs
of a deep learning framework.
We begin as before by reading the time machine dataset.


=== cell 1: code ===
%load ../utils/djl-imports
%load ../utils/plot-utils
%load ../utils/PlotUtils.java

%load ../utils/Accumulator.java
%load ../utils/Animator.java
%load ../utils/Functions.java
%load ../utils/StopWatch.java
%load ../utils/Training.java
%load ../utils/timemachine/Vocab.java
%load ../utils/timemachine/RNNModelScratch.java
%load ../utils/timemachine/TimeMachine.java

=== cell 2: code ===
import ai.djl.training.dataset.Record;

=== cell 3: code ===
NDManager manager = NDManager.newBaseManager();

=== cell 4: markdown ===
## Creating a Dataset in DJL

=== cell 5: markdown ===
In DJL, the ideal and concise way of dealing with datasets, is to use the built-in datasets that can easily wrap around existing NDArrays or to create your own dataset that extends from the `RandomAccessDataset` class. For this section, we will be implementing our own. For more information on creating your own dataset in DJL, you can refer to: https://djl.ai/docs/development/how_to_use_dataset.html

Our implementation of `TimeMachineDataset` will be a concise replacement of the `SeqDataLoader` class previously created. Using a dataset in DJL format, will allow us to use already built-in functions so we don't have to implement most things from scratch. We have to implement a Builder, a prepare function which will contain the process to save the data to the TimeMachineDataset object, and finally a get function.

=== cell 6: code ===
public static class TimeMachineDataset extends RandomAccessDataset {

    private Vocab vocab;
    private NDArray data;
    private NDArray labels;
    private int numSteps;
    private int maxTokens;
    private int batchSize;
    private NDManager manager;
    private boolean prepared;

    public TimeMachineDataset(Builder builder) {
        super(builder);
        this.numSteps = builder.numSteps;
        this.maxTokens = builder.maxTokens;
        this.batchSize = builder.getSampler().getBatchSize();
        this.manager = builder.manager;
        this.data = this.manager.create(new Shape(0,35), DataType.INT32);
        this.labels = this.manager.create(new Shape(0,35), DataType.INT32);
        this.prepared = false;
    }

    @Override
    public Record get(NDManager manager, long index) throws IOException {
        NDArray X = data.get(new NDIndex("{}", index));
        NDArray Y = labels.get(new NDIndex("{}", index));
        return new Record(new NDList(X), new NDList(Y));
    }

    @Override
    protected long availableSize() {
        return data.getShape().get(0);
    }

    @Override
    public void prepare(Progress progress) throws IOException, TranslateException {
        if (prepared) {
            return;
        }

        Pair<List<Integer>, Vocab> corpusVocabPair = null;
        try {
            corpusVocabPair = TimeMachine.loadCorpusTimeMachine(maxTokens);
        } catch (Exception e) {
            e.printStackTrace(); // Exception can be from unknown token type during tokenize() function.
        }
        List<Integer> corpus = corpusVocabPair.getKey();
        this.vocab = corpusVocabPair.getValue();

        // Start with a random offset (inclusive of `numSteps - 1`) to partition a
        // sequence
        int offset = new Random().nextInt(numSteps);
        int numTokens = ((int) ((corpus.size() - offset - 1) / batchSize)) * batchSize;
        NDArray Xs =
                manager.create(
                        corpus.subList(offset, offset + numTokens).stream()
                                .mapToInt(Integer::intValue)
                                .toArray());
        NDArray Ys =
                manager.create(
                        corpus.subList(offset + 1, offset + 1 + numTokens).stream()
                                .mapToInt(Integer::intValue)
                                .toArray());
        Xs = Xs.reshape(new Shape(batchSize, -1));
        Ys = Ys.reshape(new Shape(batchSize, -1));
        int numBatches = (int) Xs.getShape().get(1) / numSteps;

        NDList xNDList = new NDList();
        NDList yNDList = new NDList();
        for (int i = 0; i < numSteps * numBatches; i += numSteps) {
            NDArray X = Xs.get(new NDIndex(":, {}:{}", i, i + numSteps));
            NDArray Y = Ys.get(new NDIndex(":, {}:{}", i, i + numSteps));
            xNDList.add(X);
            yNDList.add(Y);
        }
        this.data = NDArrays.concat(xNDList);
        xNDList.close();
        this.labels = NDArrays.concat(yNDList);
        yNDList.close();
        this.prepared = true;
    }

    public Vocab getVocab() {
        return this.vocab;
    }

    public static final class Builder extends BaseBuilder<Builder> {
        int numSteps;
        int maxTokens;
        NDManager manager;

        @Override
        protected Builder self() { return this; }

        public Builder setSteps(int steps) {
            this.numSteps = steps;
            return this;
        }

        public Builder setMaxTokens(int maxTokens) {
            this.maxTokens = maxTokens;
            return this;
        }

        public Builder setManager(NDManager manager) {
            this.manager = manager;
            return this;
        }

        public TimeMachineDataset build() throws IOException, TranslateException {
            TimeMachineDataset dataset = new TimeMachineDataset(this);
            return dataset;
        }
    }
}

=== cell 7: markdown ===
Consequently we will update our code from the previous section for the functions `predictCh8`, `trainCh8`, `trainEpochCh8`, and `gradClipping` to include the dataset logic and also allow the functions to accept an `AbstractBlock` from DJL instead of just accepting `RNNModelScratch`.

=== cell 8: code ===
/** Generate new characters following the `prefix`. */
public static String predictCh8(
        String prefix,
        int numPreds,
        Object net,
        Vocab vocab,
        Device device,
        NDManager manager) {

    List<Integer> outputs = new ArrayList<>();
    outputs.add(vocab.getIdx("" + prefix.charAt(0)));
    Functions.SimpleFunction<NDArray> getInput =
            () ->
                    manager.create(outputs.get(outputs.size() - 1))
                            .toDevice(device, false)
                            .reshape(new Shape(1, 1));

    if (net instanceof RNNModelScratch) {
        RNNModelScratch castedNet = (RNNModelScratch) net;
        NDList state = castedNet.beginState(1, device);

        for (char c : prefix.substring(1).toCharArray()) { // Warm-up period
            state = (NDList) castedNet.forward(getInput.apply(), state).getValue();
            outputs.add(vocab.getIdx("" + c));
        }

        NDArray y;
        for (int i = 0; i < numPreds; i++) {
            Pair<NDArray, NDList> pair = castedNet.forward(getInput.apply(), state);
            y = pair.getKey();
            state = pair.getValue();

            outputs.add((int) y.argMax(1).reshape(new Shape(1)).getLong(0L));
        }
    } else {
        AbstractBlock castedNet = (AbstractBlock) net;
        NDList state = null;
        for (char c : prefix.substring(1).toCharArray()) { // Warm-up period
            if (state == null) {
                // Begin state
                state =
                        castedNet
                                .forward(
                                        new ParameterStore(manager, false),
                                        new NDList(getInput.apply()),
                                        false)
                                .subNDList(1);
            } else {
                state =
                        castedNet
                                .forward(
                                        new ParameterStore(manager, false),
                                        new NDList(getInput.apply()).addAll(state),
                                        false)
                                .subNDList(1);
            }
            outputs.add(vocab.getIdx("" + c));
        }

        NDArray y;
        for (int i = 0; i < numPreds; i++) {
            NDList pair =
                    castedNet.forward(
                            new ParameterStore(manager, false),
                            new NDList(getInput.apply()).addAll(state),
                            false);
            y = pair.get(0);
            state = pair.subNDList(1);

            outputs.add((int) y.argMax(1).reshape(new Shape(1)).getLong(0L));
        }
    }

    StringBuilder output = new StringBuilder();
    for (int i : outputs) {
        output.append(vocab.idxToToken.get(i));
    }
    return output.toString();
}

=== cell 9: code ===
/** Train a model. */
public static void trainCh8(
        Object net,
        RandomAccessDataset dataset,
        Vocab vocab,
        int lr,
        int numEpochs,
        Device device,
        boolean useRandomIter,
        NDManager manager)
        throws IOException, TranslateException {
    SoftmaxCrossEntropyLoss loss = new SoftmaxCrossEntropyLoss();
    Animator animator = new Animator();

    Functions.voidTwoFunction<Integer, NDManager> updater;
    if (net instanceof RNNModelScratch) {
        RNNModelScratch castedNet = (RNNModelScratch) net;
        updater =
                (batchSize, subManager) ->
                        Training.sgd(castedNet.params, lr, batchSize, subManager);
    } else {
        // Already initialized net
        AbstractBlock castedNet = (AbstractBlock) net;
        Model model = Model.newInstance("model");
        model.setBlock(castedNet);

        Tracker lrt = Tracker.fixed(lr);
        Optimizer sgd = Optimizer.sgd().setLearningRateTracker(lrt).build();

        DefaultTrainingConfig config =
                new DefaultTrainingConfig(loss)
                        .optOptimizer(sgd) // Optimizer (loss function)
                        .optInitializer(
                                new NormalInitializer(0.01f),
                                Parameter.Type.WEIGHT) // setting the initializer
                        .optDevices(Engine.getInstance().getDevices(1)) // setting the number of GPUs needed
                        .addEvaluator(new Accuracy()) // Model Accuracy
                        .addTrainingListeners(TrainingListener.Defaults.logging()); // Logging

        Trainer trainer = model.newTrainer(config);
        updater = (batchSize, subManager) -> trainer.step();
    }

    Function<String, String> predict =
            (prefix) -> predictCh8(prefix, 50, net, vocab, device, manager);
    // Train and predict
    double ppl = 0.0;
    double speed = 0.0;
    for (int epoch = 0; epoch < numEpochs; epoch++) {
        Pair<Double, Double> pair =
                trainEpochCh8(net, dataset, loss, updater, device, useRandomIter, manager);
        ppl = pair.getKey();
        speed = pair.getValue();
        if ((epoch + 1) % 10 == 0) {
           animator.add(epoch + 1, (float) ppl, "ppl");
           animator.show();
        }
    }
    System.out.format(
            "perplexity: %.1f, %.1f tokens/sec on %s%n", ppl, speed, device.toString());
    System.out.println(predict.apply("time traveller"));
    System.out.println(predict.apply("traveller"));
}

=== cell 10: code ===
/** Train a model within one epoch. */
public static Pair<Double, Double> trainEpochCh8(
        Object net,
        RandomAccessDataset dataset,
        Loss loss,
        Functions.voidTwoFunction<Integer, NDManager> updater,
        Device device,
        boolean useRandomIter,
        NDManager manager)
        throws IOException, TranslateException {
    StopWatch watch = new StopWatch();
    watch.start();
    Accumulator metric = new Accumulator(2); // Sum of training loss, no. of tokens

    try (NDManager childManager = manager.newSubManager()) {
        NDList state = null;
        for (Batch batch : dataset.getData(childManager)) {
            NDArray X = batch.getData().head().toDevice(device, true);
            NDArray Y = batch.getLabels().head().toDevice(device, true);
            if (state == null || useRandomIter) {
                // Initialize `state` when either it is the first iteration or
                // using random sampling
                if (net instanceof RNNModelScratch) {
                    state =
                            ((RNNModelScratch) net)
                                    .beginState((int) X.getShape().getShape()[0], device);
                }
            } else {
                for (NDArray s : state) {
                    s.stopGradient();
                }
            }
            if (state != null) {
                state.attach(childManager);
            }

            NDArray y = Y.transpose().reshape(new Shape(-1));
            X = X.toDevice(device, false);
            y = y.toDevice(device, false);
            try (GradientCollector gc = Engine.getInstance().newGradientCollector()) {
                NDArray yHat;
                if (net instanceof RNNModelScratch) {
                    Pair<NDArray, NDList> pairResult = ((RNNModelScratch) net).forward(X, state);
                    yHat = pairResult.getKey();
                    state = pairResult.getValue();
                } else {
                    NDList pairResult;
                    if (state == null) {
                        // Begin state
                        pairResult =
                                ((AbstractBlock) net)
                                        .forward(
                                                new ParameterStore(manager, false),
                                                new NDList(X),
                                                true);
                    } else {
                        pairResult =
                                ((AbstractBlock) net)
                                        .forward(
                                                new ParameterStore(manager, false),
                                                new NDList(X).addAll(state),
                                                true);
                    }
                    yHat = pairResult.get(0);
                    state = pairResult.subNDList(1);
                }

                NDArray l = loss.evaluate(new NDList(y), new NDList(yHat)).mean();
                gc.backward(l);
                metric.add(new float[] {l.getFloat() * y.size(), y.size()});
            }
            gradClipping(net, 1, childManager);
            updater.apply(1, childManager); // Since the `mean` function has been invoked
        }
    }
    return new Pair<>(Math.exp(metric.get(0) / metric.get(1)), metric.get(1) / watch.stop());
}

=== cell 11: code ===
/** Clip the gradient. */
public static void gradClipping(Object net, int theta, NDManager manager) {
    double result = 0;
    NDList params;
    if (net instanceof RNNModelScratch) {
        params = ((RNNModelScratch) net).params;
    } else {
        params = new NDList();
        for (Pair<String, Parameter> pair : ((AbstractBlock) net).getParameters()) {
            params.add(pair.getValue().getArray());
        }
    }
    for (NDArray p : params) {
        NDArray gradient = p.getGradient().stopGradient();
        gradient.attach(manager);
        result += gradient.pow(2).sum().getFloat();
    }
    double norm = Math.sqrt(result);
    if (norm > theta) {
        for (NDArray param : params) {
            NDArray gradient = param.getGradient();
            gradient.muli(theta / norm);
        }
    }
}

=== cell 12: markdown ===
Now we will leverage the dataset that we just created and assign the required parameters.

=== cell 13: code ===
int batchSize = 32;
int numSteps = 35;

TimeMachineDataset dataset = new TimeMachineDataset.Builder()
        .setManager(manager).setMaxTokens(10000).setSampling(batchSize, false)
        .setSteps(numSteps).build();
dataset.prepare();
Vocab vocab = dataset.getVocab();

=== cell 14: markdown ===
## Defining the Model

High-level APIs provide implementations of recurrent neural networks.
We construct the recurrent neural network layer `rnn_layer` with a single hidden layer and 256 hidden units.
In fact, we have not even discussed yet what it means to have multiple layers---this will happen in :numref:`sec_deep_rnn`.
For now, suffice it to say that multiple layers simply amount to the output of one layer of RNN being used as the input for the next layer of RNN.


=== cell 15: code ===
int numHiddens = 256;
RNN rnnLayer = RNN.builder().setNumLayers(1)
        .setStateSize(numHiddens).optReturnState(true).optBatchFirst(false).build();

=== cell 16: markdown ===
Initializing the hidden state is straightforward.
We invoke the member function `beginState` _(In DJL we don't have to run `beginState` to later specify the resulting state the first time we run `forward`, as this logic is ran by DJL the first time we do `forward` but we will create it here for demonstration purposes)_.
This returns a list (`state`)
that contains
an initial hidden state
for each example in the minibatch,
whose shape is
(number of hidden layers, batch size, number of hidden units).
For some models 
to be introduced later 
(e.g., long short-term memory),
such a list also
contains other information.

=== cell 17: code ===
public static NDList beginState(int batchSize, int numLayers, int numHiddens) {
    return new NDList(manager.zeros(new Shape(numLayers, batchSize, numHiddens)));
}

NDList state = beginState(batchSize, 1, numHiddens);
System.out.println(state.size());
System.out.println(state.get(0).getShape());

=== cell 18: markdown ===
With a hidden state and an input,
we can compute the output with
the updated hidden state.
It should be emphasized that
the "output" (`Y`) of `rnnLayer`
does *not* involve computation of output layers:
it refers to 
the hidden state at *each* time step,
and they can be used as the input
to the subsequent output layer.

=== cell 19: markdown ===
Besides,
the updated hidden state (`stateNew`) returned by `rnnLayer`
refers to the hidden state
at the *last* time step of the minibatch.
It can be used to initialize the 
hidden state for the next minibatch within an epoch
in sequential partitioning.
For multiple hidden layers,
the hidden state of each layer will be stored
in this variable (`stateNew`).
For some models 
to be introduced later 
(e.g., long short-term memory),
this variable also
contains other information.

=== cell 20: code ===
NDArray X = manager.randomUniform (0, 1,new Shape(numSteps, batchSize, vocab.length()));

NDList input = new NDList(X, state.get(0));
rnnLayer.initialize(manager, DataType.FLOAT32, input.getShapes());
NDList forwardOutput = rnnLayer.forward(new ParameterStore(manager, false), input, false);
NDArray Y = forwardOutput.get(0);
NDArray stateNew = forwardOutput.get(1);

System.out.println(Y.getShape());
System.out.println(stateNew.getShape());

=== cell 21: markdown ===
Similar to :numref:`sec_rnn_scratch`,
we define an `RNNModel` class 
for a complete RNN model.
Note that `rnnLayer` only contains the hidden recurrent layers, we need to create a separate output layer.

=== cell 22: code ===
public class RNNModel extends AbstractBlock {

    private RNN rnnLayer;
    private Linear dense;
    private int vocabSize;

    public RNNModel(RNN rnnLayer, int vocabSize) {
        this.rnnLayer = rnnLayer;
        this.addChildBlock("rnn", rnnLayer);
        this.vocabSize = vocabSize;
        this.dense = Linear.builder().setUnits(vocabSize).build();
        this.addChildBlock("linear", dense);
    }

    @Override
    protected NDList forwardInternal(ParameterStore parameterStore, NDList inputs, boolean training, PairList<String, Object> params) {
        NDArray X = inputs.get(0).transpose().oneHot(vocabSize);
        inputs.set(0, X);
        NDList result = rnnLayer.forward(parameterStore, inputs, training);
        NDArray Y = result.get(0);
        NDArray state = result.get(1);

        int shapeLength = Y.getShape().dimension();
        NDList output = dense.forward(parameterStore, new NDList(Y
                .reshape(new Shape(-1, Y.getShape().get(shapeLength-1)))), training);
        return new NDList(output.get(0), state);
    }
    
    @Override
    public void initializeChildBlocks(NDManager manager, DataType dataType, Shape... inputShapes) {
        Shape shape = rnnLayer.getOutputShapes(new Shape[]{inputShapes[0]})[0];
        dense.initialize(manager, dataType, new Shape(vocabSize, shape.get(shape.dimension() - 1)));
    }

    /* We won't implement this since we won't be using it but it's required as part of an AbstractBlock  */
    @Override
    public Shape[] getOutputShapes(Shape[] inputShapes) {
        return new Shape[0];
    }
}

=== cell 23: markdown ===
## Training and Predicting

Before training the model, let us make a prediction with the a model that has random weights.


=== cell 24: code ===
Device device = manager.getDevice();
RNNModel net = new RNNModel(rnnLayer, vocab.length());
net.initialize(manager, DataType.FLOAT32, X.getShape());
predictCh8("time traveller", 10, net, vocab, device, manager);

=== cell 25: markdown ===
As is quite obvious, this model does not work at all. Next, we call `trainCh8` with the same hyperparameters defined in :numref:`sec_rnn_scratch` and train our model with high-level APIs.


=== cell 26: code ===
int numEpochs = Integer.getInteger("MAX_EPOCH", 500);

int lr = 1;
trainCh8((Object) net, dataset, vocab, lr, numEpochs, device, false, manager);

=== cell 27: markdown ===
Compared with the last section, this model achieves comparable perplexity,
albeit within a shorter period of time, due to the code being more optimized by
high-level APIs of the deep learning framework.


## Summary

* High-level APIs of the deep learning framework provides an implementation of the RNN layer.
* The RNN layer of high-level APIs returns an output and an updated hidden state, where the output does not involve output layer computation.
* Using high-level APIs leads to faster RNN training than using its implementation from scratch.

## Exercises

1. Can you make the RNN model overfit using the high-level APIs?
1. What happens if you increase the number of hidden layers in the RNN model? Can you make the model work?
1. Implement the autoregressive model of :numref:`sec_sequence` using an RNN.
