# Root directory of the repository

# Dockerfile for a Python application using raftos
# This Dockerfile is designed to build a Docker for our repository
# It installs the necessary dependencies, including raftos, and applies a patch to make it compatible with modern cryptography versions.
# Dependencies can be found in requirements-main.txt

FROM python:3.10-slim
WORKDIR /src

# Copy and install main requirements first (without raftos)
COPY requirements-main.txt .
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements-main.txt

# Install raftos with --no-deps to avoid cryptography conflict
RUN pip install raftos==0.2.6 --no-deps

# Copy the application code
COPY src/ /src/
# Copy the patch script 
COPY patch_raftos.py /src/
# Apply the patch to make raftos work with modern cryptography
RUN python /src/patch_raftos.py

ENV PYTHONPATH=/src
CMD ["python", "app/main.py"]