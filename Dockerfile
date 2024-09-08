FROM python:3.12.5

WORKDIR /opt/docker/body-track-project
RUN mkdir -p /opt/docker/body-track-project
COPY . /opt/docker/body-track-project/

RUN chmod +x /opt/docker/body-track-project/svc.sh
RUN chmod -R 755 /opt/docker/body-track-project
RUN ls -la /opt/docker/body-track-project/

RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

RUN /opt/docker/body-track-project/svc.sh --help
RUN /opt/docker/body-track-project/svc.sh build

# EXPOSE 10000
# CMD ["/opt/docker/body-track-project/svc.sh", "start"]