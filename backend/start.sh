#!/bin/bash
cd /opt/render/project/src/backend
uvicorn main:app --host 0.0.0.0 --port $PORT

# Made with Bob
