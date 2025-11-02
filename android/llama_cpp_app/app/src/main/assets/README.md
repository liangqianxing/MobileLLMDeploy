This directory stores runtime assets for the demo app.

Place quantized model weights under the `models/` subfolder, e.g. by running the helper scripts from the repository root:

```
python scripts/download_model.py --repo qwen/Qwen2.5-1.5B-Instruct --output models/qwen2.5-1.5b
```

Convert the weights to GGUF (or your desired format) before copying them into `models/`.
