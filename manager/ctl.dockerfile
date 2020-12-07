FROM debian:latest

COPY tunasynctl /usr/bin

RUN chmod +x /usr/bin/tunasynctl
