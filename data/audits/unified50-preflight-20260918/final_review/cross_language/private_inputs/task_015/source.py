=== cell 0: markdown ===
# Concise Implementation of Multilayer Perceptron

:label:`sec_mlp_djl`


As you might expect, by relying on the DJL library,
we can implement MLPs even more concisely. <br>
Let's setup the relevant libraries first.

=== cell 1: code ===
%load ../utils/djl-imports
%load ../utils/plot-utils

=== cell 2: code ===
import ai.djl.metric.*;
import ai.djl.basicdataset.cv.classification.*;
import org.apache.commons.lang3.ArrayUtils;

=== cell 3: markdown ===
## The Model

As compared to our concise implementation 
of softmax regression implementation
(:numref:`sec_softmax_djl`),
the only difference is that we add 
*two* `Linear` (fully-connected) layers 
(previously, we added *one*).
The first is our hidden layer, 
which contains *256* hidden units
and applies the ReLU activation function.
The second is our output layer.

=== cell 4: code ===
SequentialBlock net = new SequentialBlock();
net.add(Blocks.batchFlattenBlock(784));
net.add(Linear.builder().setUnits(256).build());
net.add(Activation::relu);
net.add(Linear.builder().setUnits(10).build());
net.setInitializer(new NormalInitializer(), Parameter.Type.WEIGHT);

=== cell 5: markdown ===
Note that DJL, as usual, automatically
infers the missing input dimensions to each layer.

The training loop is *exactly* the same
as when we implemented softmax regression.
This modularity enables us to separate 
matters concerning the model architecture
from orthogonal considerations.

=== cell 6: code ===
int batchSize = 256;
int numEpochs = Integer.getInteger("MAX_EPOCH", 10);
double[] trainLoss;
double[] testAccuracy;
double[] epochCount;
double[] trainAccuracy;

trainLoss = new double[numEpochs];
trainAccuracy = new double[numEpochs];
testAccuracy = new double[numEpochs];
epochCount = new double[numEpochs];

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

for(int i = 0; i < epochCount.length; i++) {
    epochCount[i] = (i + 1);
}

Map<String, double[]> evaluatorMetrics = new HashMap<>();

=== cell 7: code ===
Tracker lrt = Tracker.fixed(0.5f);
Optimizer sgd = Optimizer.sgd().setLearningRateTracker(lrt).build();

Loss loss = Loss.softmaxCrossEntropyLoss();

DefaultTrainingConfig config = new DefaultTrainingConfig(loss)
                .optOptimizer(sgd) // Optimizer (loss function)
                .optDevices(Engine.getInstance().getDevices(1)) // single GPU
                .addEvaluator(new Accuracy()) // Model Accuracy
                .addTrainingListeners(TrainingListener.Defaults.logging()); // Logging

    try (Model model = Model.newInstance("mlp")) {
        model.setBlock(net);

        try (Trainer trainer = model.newTrainer(config)) {

            trainer.initialize(new Shape(1, 784));
            trainer.setMetrics(new Metrics());

            EasyTrain.fit(trainer, numEpochs, trainIter, testIter);
            // collect results from evaluators
            Metrics metrics = trainer.getMetrics();

            trainer.getEvaluators().stream()
                    .forEach(evaluator -> {
                        evaluatorMetrics.put("train_epoch_" + evaluator.getName(), metrics.getMetric("train_epoch_" + evaluator.getName()).stream()
                                            .mapToDouble(x -> x.getValue().doubleValue()).toArray());
                        evaluatorMetrics.put("validate_epoch_" + evaluator.getName(), metrics.getMetric("validate_epoch_" + evaluator.getName()).stream()
                                            .mapToDouble(x -> x.getValue().doubleValue()).toArray());
            });
    }
}

=== cell 8: code ===
trainLoss = evaluatorMetrics.get("train_epoch_SoftmaxCrossEntropyLoss");
trainAccuracy = evaluatorMetrics.get("train_epoch_Accuracy");
testAccuracy = evaluatorMetrics.get("validate_epoch_Accuracy");

String[] lossLabel = new String[trainLoss.length + testAccuracy.length + trainAccuracy.length];

Arrays.fill(lossLabel, 0, trainLoss.length, "test acc");
Arrays.fill(lossLabel, trainAccuracy.length, trainLoss.length + trainAccuracy.length, "train acc");
Arrays.fill(lossLabel, trainLoss.length + trainAccuracy.length,
                trainLoss.length + testAccuracy.length + trainAccuracy.length, "train loss");

Table data = Table.create("Data").addColumns(
            DoubleColumn.create("epochCount", ArrayUtils.addAll(epochCount, ArrayUtils.addAll(epochCount, epochCount))),
            DoubleColumn.create("loss", ArrayUtils.addAll(testAccuracy , ArrayUtils.addAll(trainAccuracy, trainLoss))),
            StringColumn.create("lossLabel", lossLabel)
);

render(LinePlot.create("", data, "epochCount", "loss", "lossLabel"),"text/html");

=== cell 9: markdown ===
## Exercises

1. Try adding different numbers of hidden layers. What setting (keeping other parameters and hyperparameters constant) works best? 
1. Try out different activation functions. Which ones work best?
1. Try different schemes for initializing the weights. What method works best?

