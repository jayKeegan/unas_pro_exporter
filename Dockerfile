FROM python:3.12.8

# Set the working directory
WORKDIR /app

# change directory
RUN cd /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the src folder
COPY src/ .

# Run the application
CMD ["python", "main.py"]