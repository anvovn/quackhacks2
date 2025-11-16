# Use the official lightweight Python image
FROM python:3.10-slim
# Set working directory
WORKDIR /app
# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy game Python files
COPY game/*.py ./game/
# Copy templates and static folders
COPY templates ./templates
COPY static ./static
# ADDED: Copy assets folder
COPY assets ./assets
# Expose port
EXPOSE 5000
# Set Flask environment variables
ENV FLASK_APP=game/server.py
ENV FLASK_RUN_HOST=0.0.0.0
# Run the server
CMD ["python", "-u", "game/server.py"]