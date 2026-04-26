#!/bin/bash

source $HOME/LilL3x/bin/activate

pip install pyimgur
pip install google.genai

pip uninstall -y openwakeword
pip install openwakeword --no-deps
pip install onnxruntime numpy tqdm scipy requests scikit-learn
python -c "import openwakeword; openwakeword.utils.download_models()"
ln $HOME/LilL3x/lib/python3.13/site-packages/openwakeword/resources/models/*.onnx $HOME/LilL3x/wake

#pip install gpiozero

