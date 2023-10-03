#!/bin/bash

mkdir models
wget -q https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip -O /tmp/english_g2.zip
wget -q https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip -O /tmp/craft_mlt_25k.zip
unzip /tmp/english_g2.zip -d models
unzip /tmp/craft_mlt_25k.zip -d models
rm -rf /tmp/english_g2.zip
rm -rf /tmp/craft_mlt_25k.zip