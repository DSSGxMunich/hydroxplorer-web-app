# Select Python image
FROM python:3.11-slim-bookworm

# Set working directory and copy required files
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt

# Install module dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy every content from the local file to the image
COPY . /app

# Start application
ENTRYPOINT [ "python" ]
CMD ["app.py" ]