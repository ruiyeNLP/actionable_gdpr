#!/bin/bash

conda init bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate gdpr37
which python
python3 sentences_filter.py
python3 sentences_dedup.py
python3 keyword_extraction.py