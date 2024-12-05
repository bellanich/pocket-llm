# Infer poetry shell
PYTHON_SITE_PACKAGES = $(shell poetry env info -p)/lib/python3.10/site-packages

.PHONY: all install-rust install-mlc-llm apply-patches validate
all: install-rust install-mlc-llm apply-patches validate

install-rust:
	@echo "Installing rust and cargo..."
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
	@echo ""

install-mlc-llm:
	@echo "Installing MLC LLM lib..."
	poetry run python -m pip install --pre -U -f https://mlc.ai/wheels mlc-llm-cpu mlc-ai-cpu
	@echo ""

apply-patches:
	@echo "Manually adding custom patches..."
	@echo "Adding SigLIP model definitions..."
	cp models/patches/siglip_vision.py $(PYTHON_SITE_PACKAGES)/mlc_llm/model/vision/siglip_vision.py
	cp models/patches/model.py $(PYTHON_SITE_PACKAGES)/mlc_llm/model/model.py
	cp models/patches/__init__.py $(PYTHON_SITE_PACKAGES)/mlc_llm/model/vision/__init__.py
	@echo ""

	@echo "Adding Llava OneVision model definition..."
	cp -r models/patches/llava_onevision $(PYTHON_SITE_PACKAGES)/mlc_llm/model/llava_onevision
	@echo ""

validate:
	@echo "Validating MLC LLM installation..."
	poetry run python -c "import mlc_llm; print(mlc_llm)"
	@echo "Validation complete."
