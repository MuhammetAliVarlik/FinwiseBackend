#!/bin/bash
set -e

# Define model path
MODEL_FILE="/app/models/lstm_baseline.h5"

# Check if model exists
if [ ! -f "$MODEL_FILE" ]; then
    echo "⚡ Model not found at $MODEL_FILE"
    echo "⚡ Starting Automatic Training... (This may take 1-2 minutes)"
    
    # Run the training module
    python3 -m app.ml.train_lstm
    
    echo "✅ Training Complete. Model saved."
else
    echo "✅ Model found at $MODEL_FILE. Skipping training."
fi

# Execute the main command (starts Uvicorn)
exec "$@"