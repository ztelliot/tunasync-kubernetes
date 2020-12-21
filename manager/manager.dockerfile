FROM debian:latest

COPY tunasync tunasynctl /usr/bin/

RUN chmod +x /usr/bin/tunasync /usr/bin/tunasynctl && mkdir /etc/tunasync/

COPY ctl.conf manager.conf /etc/tunasync/

VOLUME ["/var/lib/tunasync"]

EXPOSE 14242

ENTRYPOINT ["/bin/bash", "-c", "(tunasync manager --config /etc/tunasync/manager.conf)"]
