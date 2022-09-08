FROM --platform=linux/amd64 python:3.10-alpine

RUN apk update && apk add --no-cache curl
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/bin sh
#RUN arduino-cli core update-index

RUN pip install --no-cache-dir pyyaml
COPY compile.py /usr/src/app/

WORKDIR /usr/src/sketch
CMD [ "python", "-u", "/usr/src/app/compile.py" ]
