FROM python:3.12.5

# Set the working directory inside the container
WORKDIR /opt/docker/body-track-project

# Copy the current directory contents into the container
COPY . /opt/docker/body-track-project/

RUN chmod +x /opt/docker/body-track-project/svc.sh

# Install system dependencies for OpenCV
RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

# Upgrade pip and install Python dependencies
RUN /opt/docker/body-track-project/svc.sh build

EXPOSE 10000

CMD ["/opt/docker/body-track-project/svc.sh", "start"]