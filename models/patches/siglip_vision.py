"""
Implements the SigLIP Vision Encoder.
"""

import dataclasses
import logging
from typing import Any, Dict, Tuple

from tvm import relax
from tvm.relax.frontend import nn
from tvm.relax.frontend.nn import Module, Tensor
from tvm.relax.frontend.nn.modules import Conv2D
from tvm.relax.frontend.nn.op import (
    add,
    broadcast_to,
    permute_dims,
    reshape,
    wrap_nested,
)
from tvm.relax.op import arange

from mlc_llm import op as op_ext
from mlc_llm.support.config import ConfigBase

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SiglipVisionConfig(ConfigBase):  # pylint: disable=too-many-instance-attributes
    """
    Config for the vision encoder
    """

    hidden_size: int = 768
    intermediate_size: int = 3072
    num_hidden_layers: int = 12
    num_attention_heads: int = 12
    num_channels: int = 3
    image_size: int = 224
    patch_size: int = 16
    hidden_act: str = "gelu_pytorch_tanh"
    layer_norm_eps: float = 1e-06
    attention_dropout: float = 0.0
    kwargs: Dict[str, Any] = dataclasses.field(default_factory=dict)


# pylint: disable=invalid-name,missing-docstring
class SiglipVisionEmbeddings(Module):  # pylint: disable=too-many-instance-attributes
    def __init__(self, config: SiglipVisionConfig):
        super().__init__()
        self.config = config
        self.embed_dim = config.hidden_size
        self.image_size = config.image_size
        self.patch_size = config.patch_size

        self.patch_embedding = Conv2D(
            in_channels=config.num_channels,
            out_channels=self.embed_dim,
            kernel_size=self.patch_size,
            stride=self.patch_size,
            bias=False,
        )

        self.num_patches = (self.image_size // self.patch_size) ** 2
        self.num_positions = self.num_patches
        self.position_embedding = nn.Embedding(num=self.num_positions, dim=self.embed_dim)

    def forward(self, pixel_values: Tensor, interpolate_pos_encoding: bool = False) -> Tensor:
        batch_size, _, height, width = pixel_values.shape
        patch_embeds = self.patch_embedding(pixel_values)  # shape = [*, width, grid, grid]
        patch_embeds = reshape(patch_embeds, shape=(batch_size, self.embed_dim, -1))
        embeddings = permute_dims(
            patch_embeds, axes=(0, 2, 1)
        )  # shape = [batch,grid*grid,embed_dim] / grid*grid=number of patches

        if interpolate_pos_encoding:
            raise NotImplementedError("Currently unsupported")

        posi_ids = reshape(
            wrap_nested(arange(0, self.num_positions, dtype="int32"), name="arange"), shape=(1, -1)
        )
        batch_position_embedding = broadcast_to(
            self.position_embedding(posi_ids),
            shape=(batch_size, self.num_positions, self.embed_dim),
        )
        embeddings = add(embeddings, batch_position_embedding)
        return embeddings


# pylint: disable=missing-docstring
def sigmoid(x: Tensor, name: str = "sigmoid") -> Tensor:
    """Sigmoid of a Tensor

    Parameters
    ----------
    x : Tensor
        Input tensor to expand.
    name : str
        Name hint for this operator.

    Returns
    -------
    result : Tensor
        Sigmoid result.
    """
    return wrap_nested(relax.op.sigmoid(x._expr), name)  # pylint: disable=protected-access


# pylint: disable=missing-docstring
def tanh(x: Tensor, name: str = "tanh") -> Tensor:
    """Tanh of a Tensor

    Parameters
    ----------
    x : Tensor
        Input tensor to expand.
    name : str
        Name hint for this operator.

    Returns
    -------
    result : Tensor
        Tanh result.
    """
    return wrap_nested(relax.op.tanh(x._expr), name)  # pylint: disable=protected-access


class QuickGELU(Module):
    def forward(self, input_tensor: Tensor) -> Tensor:
        # TODO: Use the original tanh version - currently using sigmoid for reproducibility.
        return input_tensor * sigmoid(input_tensor * 1.702)


class SiglipMLP(Module):
    def __init__(self, config: SiglipVisionConfig):
        super().__init__()
        self.activation_fn = QuickGELU()
        self.fc1 = nn.Linear(config.hidden_size, config.intermediate_size)
        self.fc2 = nn.Linear(config.intermediate_size, config.hidden_size)

    def forward(self, hidden_states: Tensor) -> Tensor:
        hidden_states = self.fc1(hidden_states)
        hidden_states = self.activation_fn(hidden_states)
        hidden_states = self.fc2(hidden_states)
        return hidden_states


class SiglipAttention(Module):  # pylint: disable=too-many-instance-attributes
    def __init__(self, config: SiglipVisionConfig):
        super().__init__()
        self.embed_dim = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = self.embed_dim // self.num_heads
        if (self.head_dim * self.num_heads) != self.embed_dim:
            raise ValueError(
                f"embed_dim must be divisible by num_heads (got `embed_dim`: {self.embed_dim}"
                f" and `num_heads`: {self.num_heads})."
            )
        self.scale = self.head_dim**-0.5
        # Ignore attention dropout as we only perform inference.
        self.k_proj = nn.Linear(self.embed_dim, self.embed_dim)
        self.v_proj = nn.Linear(self.embed_dim, self.embed_dim)
        self.q_proj = nn.Linear(self.embed_dim, self.embed_dim)
        self.out_proj = nn.Linear(self.embed_dim, self.embed_dim)

    def forward(
        self,
        hidden_states: Tensor,
    ) -> Tensor:
        d, h = self.head_dim, self.num_heads
        b, s, _ = hidden_states.shape  # batch_size, seq_len, embed_dim

        q = self.q_proj(hidden_states).reshape(b, s, h, d)
        k = self.k_proj(hidden_states).reshape(b, s, h, d)
        v = self.v_proj(hidden_states).reshape(b, s, h, d)

        attn_output = op_ext.attention(q, k, v, None)
        attn_output = self.out_proj(attn_output)
        return attn_output


class SiglipEncoderLayer(Module):
    def __init__(self, config: SiglipVisionConfig):
        super().__init__()
        self.embed_dim = config.hidden_size
        self.self_attn = SiglipAttention(config)
        self.layer_norm1 = nn.LayerNorm(normalized_shape=self.embed_dim, eps=config.layer_norm_eps)
        self.mlp = SiglipMLP(config)
        self.layer_norm2 = nn.LayerNorm(normalized_shape=self.embed_dim, eps=config.layer_norm_eps)

    def forward(self, hidden_states: Tensor) -> Tensor:
        residual = hidden_states
        hidden_states = self.layer_norm1(hidden_states)
        hidden_states = self.self_attn(hidden_states=hidden_states)
        hidden_states = residual + hidden_states
        residual = hidden_states
        hidden_states = self.layer_norm2(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states

        outputs = (hidden_states,)
        return outputs


class SiglipEncoder(Module):
    def __init__(self, config: SiglipVisionConfig):
        super().__init__()
        self.layers = nn.ModuleList(
            [SiglipEncoderLayer(config) for _ in range(config.num_hidden_layers)]
        )

    def forward(self, inputs_embeds: Tensor) -> Tensor:
        hidden_states = inputs_embeds
        encoder_states: Tuple[Any, ...] = ()
        for _, encoder_layer in enumerate(self.layers):
            encoder_states = encoder_states + (hidden_states,)
            layer_outputs = encoder_layer(hidden_states)
            hidden_states = layer_outputs[0]  # Output is a tuple with length 1.
        encoder_states = encoder_states + (hidden_states,)
        return encoder_states


class SiglipVisionTransformer(Module):
    def __init__(self, config: SiglipVisionConfig):
        super().__init__()
        embed_dim = config.hidden_size
        self.embeddings = SiglipVisionEmbeddings(config)
        self.encoder = SiglipEncoder(config)
        # Defined but not actually used.
        self.post_layernorm = nn.LayerNorm(embed_dim, eps=config.layer_norm_eps)

    def forward(self, pixel_values: Tensor) -> Tensor:
        hidden_states = self.embeddings(pixel_values)
        encoder_outputs = self.encoder(inputs_embeds=hidden_states)
        return encoder_outputs


class SiglipVisionModel(Module):
    def __init__(self, config: SiglipVisionConfig):
        super().__init__()
        self.vision_model = SiglipVisionTransformer(config)

    def forward(self, pixel_values: Tensor) -> Tensor:
        # Siglip Qwen2 is using last layer, CLIP pre-last due to different
        # Transformer encoder.
        return self.vision_model(pixel_values)[-1]
