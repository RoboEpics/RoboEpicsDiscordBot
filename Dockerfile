FROM python:slim

# Create non-root user
ENV USER worker
RUN addgroup --gid 1001 $USER && adduser -u 1001 --gid 1001 --shell /bin/sh --disabled-password --gecos "" $USER
WORKDIR /home/$USER

# Build
COPY --chown=$USER:$USER requirements.txt .
RUN set -eux \
        && pip --disable-pip-version-check install -U pip wheel setuptools \
        && runuser $USER -c 'pip --disable-pip-version-check install --user --no-cache-dir -r requirements.txt'

USER $USER

# Copy source
COPY --chown=$USER:$USER . .

# Run
CMD python main.py
