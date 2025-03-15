# Use the official Python 3.12 image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of application code
COPY . .

# Expose port 8080 (as thats the default port AWS apprunner uses) or whichever port your Flask app uses
EXPOSE 8080


CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]


