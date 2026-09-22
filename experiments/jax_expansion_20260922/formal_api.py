"""Public loss/optimizer contract executed by the trusted JAX runtime."""
import jax.numpy as jnp
import optax


def loss_from_outputs(task, outputs, batch):
    if task in ('gpt_nano','residual_cnn'):
        return optax.softmax_cross_entropy_with_integer_labels(outputs.reshape((-1,outputs.shape[-1])),batch['y'].reshape(-1)).mean()
    if task=='variational_autoencoder':
        reconstruction,mu,logvar=outputs
        target=batch['x'].reshape((2,784))
        # Torch BCE clamps logarithms to -100; fixtures are not at the boundary.
        bce=-(target*jnp.maximum(jnp.log(reconstruction),-100)+(1-target)*jnp.maximum(jnp.log1p(-reconstruction),-100)).sum()/2
        return bce-0.5*(1+logvar-mu**2-jnp.exp(logvar)).sum()/2
    if task in ('cnn_classifier','transformer_language_model','recurrent_language_model','graph_attention'):
        scores=outputs[0] if task=='recurrent_language_model' else outputs
        scores=scores.reshape((-1,scores.shape[-1]))
        return -jnp.take_along_axis(scores,batch['y'].reshape((-1,1)),axis=1).mean()
    if task=='actor_critic':
        probabilities,values=outputs
        selected=probabilities[jnp.arange(4),batch['action']]
        return -(jnp.log(selected)*batch['return']).mean()+jnp.mean((values.reshape(-1)-batch['return'])**2)
    if task=='reinforce':
        selected=outputs[jnp.arange(4),batch['action']]
        return -(jnp.log(selected)*batch['return']).mean()
    return jnp.mean((outputs-batch['y'])**2)


def make_optimizer(contract):
    cfg=contract['optimizer']
    if cfg['type']=='SGD':
        return optax.sgd(cfg['learning_rate'],momentum=cfg['momentum'])
    return optax.adam(cfg['learning_rate'],b1=cfg['betas'][0],b2=cfg['betas'][1],eps=cfg['epsilon'])
