#!/usr/bin/env bash


# (1) Get global filepath of root dir
LEVELS=3
DIR=$(realpath "$0")
for ((i=0; i<LEVELS; i++)); do
  DIR=$(dirname "$DIR")
done

export MLC_LLM_SOURCE_DIR="${DIR}"
echo $MLC_LLM_SOURCE_DIR

# (2) Run MLC LLM package command
mlc_llm package
