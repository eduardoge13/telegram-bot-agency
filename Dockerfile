# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# This layer will only be re-run if requirements.txt changes
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application's code
COPY . .

# Make port 8080 available
EXPOSE 8080

# Run the application with main.py
CMD ["python", "main.py"]