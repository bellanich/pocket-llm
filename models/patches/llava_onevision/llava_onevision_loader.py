"""
This file specifies how MLC's Llava parameter maps from other formats, for example HuggingFace
PyTorch, HuggingFace safetensors.
"""

import functools

import numpy as np

from mlc_llm.loader import ExternMapping
from mlc_llm.quantization import Quantization

from .llava_onevision_model import LlavaOnevisionConfig, LlavaOnevisionForCausalLM
from .llava_onevision_quantization import awq_quant


def huggingface(model_config: LlavaOnevisionConfig, quantization: Quantization) -> ExternMapping:
    """Returns a parameter mapping that maps from the names of MLC LLM parameters to
    the names of HuggingFace PyTorch parameters.

    Parameters
    ----------
    model_config : LlavaOnevisionConfig
        The configuration of the Llava model.

    quantization : Quantization
        The quantization configuration.

    Returns
    -------
    param_map : ExternMapping
        The parameter mapping from MLC to HuggingFace PyTorch.
    """
    model = LlavaOnevisionForCausalLM(model_config)
    if quantization is not None:
        model.to(quantization.model_dtype)
    _, _named_params, _ = model.export_tvm(  # type: ignore[misc]
        spec=model.get_default_spec(), allow_extern=True
    )
    named_parameters = dict(_named_params)
    print("Named parameters")
    for key in named_parameters:
        print(key, named_parameters[key])

    mapping = ExternMapping()

    for i in range(model_config.text_config.num_hidden_layers):
        # Add QKV in self attention
        attn = f"language_model.model.layers.{i}.self_attn"
        # mlc_name = f"{attn}.qkv_proj.weight"  # ORIGINAL CODE
        mlc_name = f"{attn}.c_attn.weight"
        # breakpoint()
        mlc_param = named_parameters[mlc_name]
        mapping.add_mapping(
            mlc_name,
            [
                f"{attn}.q_proj.weight",
                f"{attn}.k_proj.weight",
                f"{attn}.v_proj.weight",
            ],
            functools.partial(
                lambda q, k, v, dtype: np.concatenate([q, k, v], axis=0).astype(dtype),
                dtype=mlc_param.dtype,
            ),
        )
        mlc_name = f"{attn}.c_attn.bias"
        # breakpoint()
        mlc_param = named_parameters[mlc_name]
        mapping.add_mapping(
            mlc_name,
            [
                f"{attn}.q_proj.bias",
                f"{attn}.k_proj.bias",
                f"{attn}.v_proj.bias",
            ],
            functools.partial(
                lambda q, k, v, dtype: np.concatenate([q, k, v], axis=0).astype(dtype),
                dtype=mlc_param.dtype,
            ),
        )
        # Add gates in MLP
        mlp = f"language_model.model.layers.{i}.mlp"
        mlc_name = f"{mlp}.gate_up_proj.weight"
        mlc_param = named_parameters[mlc_name]
        mapping.add_mapping(
            mlc_name,
            [
                f"{mlp}.gate_proj.weight",
                f"{mlp}.up_proj.weight",
            ],
            functools.partial(
                lambda gate, up, dtype: np.concatenate([gate, up], axis=0).astype(dtype),
                dtype=mlc_param.dtype,
            ),
        )
        # inv_freq is not used in the model
        mapping.add_unused(f"{attn}.rotary_emb.inv_freq")

    for mlc_name, mlc_param in named_parameters.items():
        if mlc_name not in mapping.param_map:
            mapping.add_mapping(
                mlc_name,
                [mlc_name],
                functools.partial(
                    lambda x, dtype: x.astype(dtype),
                    dtype=mlc_param.dtype,
                ),
            )
    return mapping


def awq(model_config: LlavaOnevisionConfig, quantization: Quantization) -> ExternMapping:
    """Returns a parameter mapping that maps from the names of MLC LLM parameters to
    the names of AWQ parameters.
    Parameters
    ----------
    model_config : LlavaConfig
        The configuration of the Llava model.

    quantization : Quantization
        The quantization configuration.

    Returns
    -------
    param_map : ExternMapping
        The parameter mapping from MLC to AWQ.
    """
    model, _ = awq_quant(model_config, quantization)
    _, _named_params = model.export_tvm(spec=model.get_default_spec())
    named_parameters = dict(_named_params)

    mapping = ExternMapping()

    for mlc_name, mlc_param in named_parameters.items():
        if mlc_name not in mapping.param_map:
            mapping.add_mapping(
                mlc_name,
                [mlc_name],
                functools.partial(lambda x, dtype: x.astype(dtype), dtype=mlc_param.dtype),
            )
    return mapping
