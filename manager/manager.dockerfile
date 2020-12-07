FROM debian:latest

WORKDIR /app

COPY tunasync /usr/bin

RUN chmod +x /usr/bin/tunasync

COPY manager.conf .

VOLUME ["/var/lib/tunasync"]

EXPOSE 14242

ENTRYPOINT ["/bin/bash", "-c", "(tunasync manager --config /app/manager.conf)"]
