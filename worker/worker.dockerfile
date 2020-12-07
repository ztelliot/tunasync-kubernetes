FROM debian:latest

WORKDIR /app

COPY tunasync /usr/bin

RUN chmod +x /usr/bin/tunasync

RUN sed -i "s@http://deb.debian.org@http://mirrors.cqupt.edu.cn@g" /etc/apt/sources.list && sed -i "s@http://security.debian.org@http://mirrors.cqupt.edu.cn@g" /etc/apt/sources.list && apt update && apt install -y rsync && apt-get clean all

VOLUME ["/var/log/tunasync", "/data/mirrors"]

EXPOSE 6000

ENTRYPOINT ["/bin/bash", "-c", "(tunasync worker --config /app/worker.conf)"]
