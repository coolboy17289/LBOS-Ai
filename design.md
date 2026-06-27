## Python Training and Data Processing Specifics
### Data Processing (`lbos_ai/data/`):
- **Transcription**: `speech_to_text.py` wraps Whisper.cpp via `subprocess` or `ctranslate2` binding.
- **Text Cleaning**: `text_cleaner.py` uses `regex`, `ftfy`, `unicodedata`, and `boilerpipe3`.
- **Sentence Splitting**: `nltk.sent_tokenize` or `spacy` language model.
- **Q&A Generation**: 
  - Rule-based: Regex patterns for interrogative sentences.
  - Neural: Tiny T5 model (if accuracy required) but default is rule-based for speed.
- **Dataset Builder**: `dataset_builder.py` reads raw JSONL, applies pipeline, writes processed JSONL.

### Training (`lbos_ai/train/`):
- **Trainer**: `trainer.py` encapsulates training loop with framework abstraction.
- **Model Framework Agnosticism**: 
  - Primary implementation uses PyTorch for research flexibility.
  - TensorFlow/Keras implementation available in `tf_trainer.py` for production deployment.
  - Hugging Face Transformers integration for tokenizers and pre-processing utilities.
  - Framework selection via config (`framework: pytorch|tensorflow|huggingface`)
- **Model**: `model.py` defines custom Transformer(nn.Module) for PyTorch.
- **TensorFlow Model**: `tf_model.py` implements equivalent model using Keras.
- **Tokenizer**: `tokenizer.py` loads/saves HuggingFace tokenizer (fast tokenizers from `tokenizers` library).
- **Data Loader**: `data_loader.py` creates `Dataset` and `DataLoader` with dynamic padding.
- **Utilities**: 
  - `utils.py`: seed setting, mixed precision, gradient clipping.
  - `metrics.py`: perplexity, accuracy calculation.
- **Configuration**: `config.yaml` for hyperparameters (loaded via `OmegaConf` or `yaml`).

### Dependencies (Key):
- `torch>=2.0.0` (PyTorch for research/training)
- `tensorflow>=2.12.0` (TensorFlow for production serving)
- `transformers>=4.30.0` (for tokenizers only)
- `sentencepiece` (if using BPE)
- `accelerate>=0.20.0` (for multi-GPU)
- `yt-dlp>=2023.08.0`
- `whispercpp-python>=0.1.0` (or `git+https://github.com/ggerganov/whisper.cpp`)
- `newspaper3k>=0.2.8`
- `spacy>=3.5.0`
- `nltk>=3.8`
- `pandas>=2.0.0`
- `numpy>=1.24.0`
- `pyyaml>=6.0`
- `tqdm>=4.65.0`
- `redis>=4.5.0` (for job queue)
- `python-dotenv>=1.0.0` (for env vars)