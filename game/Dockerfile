# Use Python slim image
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements and install
COPY game/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary folders and files from repo root
COPY game/ ./game/
COPY assets/ ./assets/
COPY static/ ./static/
COPY templates/ ./templates/

# Expose port for WebSocket / web server
EXPOSE 8765

# Start your server
CMD ["python", "game/server.py"]
