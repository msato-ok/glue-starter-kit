ARG PYTHON_VERSION=3.7-slim-buster

FROM python:${PYTHON_VERSION}

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app
ARG USERNAME=appuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # Verify git, process tools, lsb-release (common in install instructions for CLIs) installed
  git \
  iproute2 \
  procps \
  lsb-release \
  zip \
  unzip \
  jq \
  curl \
  less \
  vim \
  ssh \
  ca-certificates \
  gnupg \
  cookiecutter \
  # docker cli - see https://docs.docker.com/engine/install/debian/
  && mkdir -p /etc/apt/keyrings \
  && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
  && echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
  && apt-get update \
  && apt-get install --no-install-recommends -y \
  docker-ce-cli \
  docker-compose-plugin \
  # awscli
  && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
  && unzip awscliv2.zip \
  && ./aws/install \
  && rm -rf ./aws \
  && pip install awscli-local[v2] \
  # Create a non-root user to use if preferred - see https://aka.ms/vscode-remote/containers/non-root-user.
  && groupadd --gid $USER_GID $USERNAME \
  && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
  # [Optional] Add sudo support for the non-root user
  && apt-get install -y sudo \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME\
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# glue
RUN git clone https://github.com/awslabs/aws-glue-libs.git -b master --depth 1 \
  && mv aws-glue-libs /opt/ \
  && chmod -R ao+wr /opt/aws-glue-libs

# make develop owner of the WORKDIR directory as well.
RUN chown -R $USERNAME:$USERNAME ${APP_HOME}

USER $USERNAME

# Install poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
ENV PATH /home/$USERNAME/.poetry/bin:${APP_HOME}/.venv/bin:$PATH:/home/$USERNAME/.local/bin
