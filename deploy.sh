#!/bin/bash
# Build image  tanpa cache
docker-compose build --no-cache ispu

# Start semua service di background
docker-compose up -d
