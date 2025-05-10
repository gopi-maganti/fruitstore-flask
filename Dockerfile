# This Dockerfile is for fruitstore-flask, a Flask application for managing a fruit store.

# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Add Label to the image
LABEL \
  name="Gopi Krishna Maganti" \
  email="gopi.maganti1998@gmail.com" \
  description="Docker container for a full-featured Flask backend powering an online fruit store. Supports user management, product catalog with image uploads, cart operations, and order processing using SQLite and RESTful APIs."

# Copy only requirements first (for better caching)
COPY requirements/base.txt ./requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose the default Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "run.py"]

