#!/bin/bash
date +%d-%m-%y/%H:%M:%S >> log.txt 2>&1
su - -c /home/quacksort/raspberry/venv_script.sh >> log.txt 2>&1

