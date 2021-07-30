# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# NOTE: DO *NOT* EDIT THIS FILE.  IT IS GENERATED.
# PLEASE UPDATE Dockerfile.txt INSTEAD OF THIS FILE
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
FROM ubuntu:bionic-20181204

LABEL authors="karthika <karthikaa08@gmail.com>"

#================================================
# Customize sources for apt-get
#================================================
RUN  echo "deb http://archive.ubuntu.com/ubuntu bionic main universe\n" > /etc/apt/sources.list \
  && echo "deb http://archive.ubuntu.com/ubuntu bionic-updates main universe\n" >> /etc/apt/sources.list \
  && echo "deb http://security.ubuntu.com/ubuntu bionic-security main universe\n" >> /etc/apt/sources.list

# No interactive frontend during docker build
ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true

#========================
# Miscellaneous packages
# Includes minimal runtime used for executing non GUI Java programs
#========================
RUN apt-get -qqy update \
  && apt-get -qqy --no-install-recommends install \
    bzip2 \
    ca-certificates \
    openjdk-8-jre-headless \
    tzdata \
    sudo \
    unzip \
    wget \
    jq \
    curl \
    supervisor \
    gnupg2 \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
  && sed -i 's/securerandom\.source=file:\/dev\/random/securerandom\.source=file:\/dev\/urandom/' ./usr/lib/jvm/java-8-openjdk-amd64/jre/lib/security/java.security

#===================
# Timezone settings
# Possible alternative: https://github.com/docker/docker/issues/3359#issuecomment-32150214
#===================
ENV TZ "UTC"
RUN echo "${TZ}" > /etc/timezone \
  && dpkg-reconfigure --frontend noninteractive tzdata



RUN apt-get update && \
apt-get install -yq gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 \
libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 \
libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 \
fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst  \
ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget default-libmysqlclient-dev libenchant-dev libleptonica-dev tesseract-ocr libtesseract-dev && \
wget https://github.com/Yelp/dumb-init/releases/download/v1.2.1/dumb-init_1.2.1_amd64.deb && \
dpkg -i dumb-init_*.deb && rm -f dumb-init_*.deb && \
apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN apt update && apt install default-jre git-all -y

# Set language to UTF8
ENV LANG="C.UTF-8"

#========================================
# Install Python3  and pip
#========================================
RUN apt-get install -y python3 && apt install -y python3-pip



#========================================
# Add normal user with passwordless sudo
#========================================
RUN useradd pptruser \
         --shell /bin/bash  \
         --create-home \
  && usermod -a -G sudo pptruser \
  && echo 'ALL ALL = (ALL) NOPASSWD: ALL' >> /etc/sudoers \
  && echo 'pptruser:secret' | chpasswd
ENV HOME=/home/pptruser

#=======================================
# Create shared / common bin directory
#=======================================
RUN  mkdir -p /opt/bin 

# Add user so we don't need --no-sandbox.
RUN  mkdir /home/pptruser/app \
  && mkdir /home/pptruser/data \
  && mkdir /home/pptruser/data/images \
  && mkdir /home/pptruser/data/logs \
  && mkdir /home/pptruser/data/db_logs \
  && mkdir /home/pptruser/data/resources \ 
	&& mkdir -p /home/pptruser/Downloads \
    && chown -R pptruser:pptruser /home/pptruser/app \
    && chown -R pptruser:pptruser /home/pptruser/data/resources \
    && chown -R pptruser:pptruser /home/pptruser/data/images \
    && chown -R pptruser:pptruser /home/pptruser/data/logs    \
    && chown -R pptruser:pptruser /home/pptruser/data/db_logs \
    && chown -R pptruser:pptruser /home/pptruser/data 
    



#======================================
# Add Grid check script
#======================================
#COPY check-grid.sh entry_point.sh /opt/bin/
# RUN chmod +x /opt/bin/check-grid.sh

COPY docker_phishmesh_puppeteer/entry_point.sh /opt/bin/

#======================================
# Add Supervisor configuration file
#======================================
COPY docker_phishmesh_puppeteer/supervisord.conf /etc
RUN  mkdir -p /var/run/supervisor /var/log/supervisor \
  && chmod -R 777 /var/run/supervisor /var/log/supervisor /etc/passwd \
  && chgrp -R 0 ${HOME} /var/run/supervisor /var/log/supervisor \
  && chmod -R g=u ${HOME} /var/run/supervisor /var/log/supervisor



#===================================================
# Run the following commands as non-privileged user
#===================================================
USER pptruser

ENTRYPOINT ["/usr/bin/dumb-init","--"]
CMD ["/opt/bin/entry_point.sh"]

USER root

#==============
# Xvfb
#==============
RUN apt-get update -qqy \
  && apt-get -qqy install \
    xvfb \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

#==============================
# Locale and encoding settings
#==============================
ENV LANG_WHICH en
ENV LANG_WHERE US
ENV ENCODING UTF-8
ENV LANGUAGE ${LANG_WHICH}_${LANG_WHERE}.${ENCODING}
ENV LANG ${LANGUAGE}
# Layer size: small: ~9 MB
# Layer size: small: ~9 MB MB (with --no-install-recommends)
RUN apt-get -qqy update \
  && apt-get -qqy --no-install-recommends install \
    language-pack-en \
    tzdata \
    locales \
  && locale-gen ${LANGUAGE} \
  && dpkg-reconfigure --frontend noninteractive locales \
  && apt-get -qyy autoremove \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get -qyy clean

#================
# Font libraries
#================
# libfontconfig            ~1 MB
# libfreetype6             ~1 MB
# xfonts-cyrillic          ~2 MB
# xfonts-scalable          ~2 MB
# fonts-liberation         ~3 MB
# fonts-ipafont-gothic     ~13 MB
# fonts-wqy-zenhei         ~17 MB
# fonts-tlwg-loma-otf      ~300 KB
# ttf-ubuntu-font-family   ~5 MB
#   Ubuntu Font Family, sans-serif typeface hinted for clarity
# Removed packages:
# xfonts-100dpi            ~6 MB
# xfonts-75dpi             ~6 MB
# Regarding fonts-liberation see:
#  https://github.com/SeleniumHQ/docker-selenium/issues/383#issuecomment-278367069
# Layer size: small: 36.28 MB (with --no-install-recommends)
# Layer size: small: 36.28 MB
RUN apt-get -qqy update \
  && apt-get -qqy --no-install-recommends install \
    libfontconfig \
    libfreetype6 \
    xfonts-cyrillic \
    xfonts-scalable \
    fonts-liberation \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-tlwg-loma-otf \
    ttf-ubuntu-font-family \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get -qyy clean

#===================================================
# Run the following commands as non-privileged user
#===================================================


USER pptruser

# #==============================
# # Scripts to run XVFB
# #==============================
COPY docker_phishmesh_puppeteer/start-xvfb.sh \
      /opt/bin/



#============================
# Some configuration options
#============================
ENV SCREEN_WIDTH 1360
ENV SCREEN_HEIGHT 1020
ENV SCREEN_DEPTH 24
ENV DISPLAY :99.0
ENV START_XVFB true


# Following line fixes https://github.com/SeleniumHQ/docker-selenium/issues/87
ENV DBUS_SESSION_BUS_ADDRESS=/dev/null

# Creating base directory for Xvfb
RUN  sudo mkdir -p /tmp/.X11-unix && sudo chmod 1777 /tmp/.X11-unix

USER root


RUN chmod +x /opt/bin/start-xvfb.sh


USER pptruser

USER root

#=====
# VNC
#=====
RUN apt-get update -qqy \
  && apt-get -qqy install \
  x11vnc \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

#=========
# fluxbox
# A fast, lightweight and responsive window manager
#=========
RUN apt-get update -qqy \
  && apt-get -qqy install \
    fluxbox \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

USER pptruser

#==============================
# Generating the VNC password as pptruser
# So the service can be started with pptruser
#==============================

RUN mkdir -p ${HOME}/.vnc \
  && x11vnc -storepasswd secret ${HOME}/.vnc/passwd

#==========
# Relaxing permissions for OpenShift and other non-sudo environments
#==========
RUN sudo chmod -R 777 ${HOME} \
  && sudo chgrp -R 0 ${HOME} \
  && sudo chmod -R g=u ${HOME}

#==============================
# Scripts to run fluxbox and x11vnc
#==============================
COPY docker_phishmesh_puppeteer/start-fluxbox.sh \
      docker_phishmesh_puppeteer/start-vnc.sh \
      /opt/bin/


USER root

RUN sudo chmod +x /opt/bin/start-fluxbox.sh
RUN sudo chmod +x /opt/bin/start-vnc.sh




COPY data/keys/github_key_phishmesh .
#ADD PhishMeshCrawler /home/pptruser/app



RUN chown -R pptruser:pptruser github_key_phishmesh

RUN eval "$(ssh-agent -s)" \
    && ssh-add github_key_phishmesh \
    && ssh-keyscan -H github.com >> /etc/ssh/ssh_known_hosts \
    && cd /home/pptruser/app && pwd \
    && git init \ 
    && git remote add -f origin git@github.com:karthikaS03/PhishMesh.git \
    && git config core.sparsecheckout true \
    && echo 'PhishMeshCrawler' >> .git/info/sparse-checkout \
    && git pull origin master



RUN chown -R pptruser:pptruser /home/pptruser/



# Install python dependencies
COPY docker_phishmesh_puppeteer/python_reqs.txt /tmp/python_reqs.txt
COPY docker_phishmesh_puppeteer/python_reqs_pre.txt /tmp/python_reqs_pre.txt
RUN pip3 install -r /tmp/python_reqs_pre.txt  
RUN pip3 install -r /tmp/python_reqs.txt
#RUN pip3 install $(grep -vE "^\s*#" /tmp/python_reqs.txt  | tr "\n" " ")

USER pptruser

#==============================
# Supervisor configuration file
#==============================
COPY docker_phishmesh_puppeteer/display.conf /etc/supervisor/conf.d/


EXPOSE 4444
EXPOSE 5900


USER pptruser

WORKDIR /home/pptruser/app/PhishMeshCrawler
