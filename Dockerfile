# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /code

# Copy the requirements file into the container
COPY ./requirements.txt /code/requirements.txt

# Install the Python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create a user to avoid running as root (required for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy the application code
COPY --chown=user . /code

# Command to run the FastAPI application on port 7860 (default for HF Spaces)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
