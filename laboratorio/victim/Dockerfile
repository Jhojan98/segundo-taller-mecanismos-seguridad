FROM alpine:3.20

RUN apk add --no-cache nginx openssh-server python3 busybox-extras tzdata

COPY banners.py /opt/banners.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 21 22 23 80 8080 4444
CMD ["/entrypoint.sh"]
