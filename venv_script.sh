#!/bin/bash
cd /home/quacksort/raspberry
source venv/bin/activate
python update_wg_config.py >> log.txt 2>&1
