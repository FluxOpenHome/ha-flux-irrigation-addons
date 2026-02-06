ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip

# Copy requirements and install
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Copy application
COPY app/ /app/
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
