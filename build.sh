#!/bin/bash

# Check and install dependencies
pip install nuitka --break-system-packages
pip install PyQt6 --break-system-packages
pip install PyQt6-WebEngine --break-system-packages
pip install gitpython --break-system-packages

# Create dist directory
mkdir -p dist

# Build RytonStudio
python3 -m nuitka \
    --jobs=10 --follow-imports --plugin-enable=pyqt6 --standalone \
    --include-data-dir=src/main/icons=icons \
    --include-data-dir=src/main/images=images \
    --include-data-dir=src/main/fonts=fonts \
    --include-data-dir=src/main/widgets=widgets \
    --nofollow-import-to==anthropic \
    --nofollow-import-to==google.generativeai \
    --output-dir=dist \
    --show-progress \
    --experimental=allow-c-warnings \
    --debug \
    src/main/main.py