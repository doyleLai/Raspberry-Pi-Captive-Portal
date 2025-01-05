#!/bin/bash
echo "Run starthostapd.sh $(date)" >> hostapd_log
./starthostapd.sh >> hostapd_log 2>&1
python3 captiveserver.py
