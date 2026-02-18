# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory to /code
WORKDIR /code

# Copy the requirements file into the container at /code
COPY ./requirements.txt /code/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of your app's code
COPY . /code

# Create a writable directory for the database (since you use sqlite3)
RUN chmod 777 /code

# Start the Flask app using Gunicorn on port 7860 (Required for Hugging Face)
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
