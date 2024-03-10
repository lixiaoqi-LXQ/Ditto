FROM ubuntu:20.04

RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list
RUN apt update -yqq

RUN DEBIAN_FRONTEND=noninteractive apt install -yqq\
    sudo build-essential cmake wget curl git python3 pip lsb-release zsh\
    vim iproute2 net-tools\
    libmemcached-dev memcached libboost-all-dev redis libhiredis-dev
RUN pip install gdown python-memcached fabric

# system setup
RUN useradd -m user && usermod -aG sudo user && chsh -s /usr/bin/zsh
RUN echo "root:123\nuser:123" | chpasswd
RUN echo "Ditto" > /etc/hostname

WORKDIR /home/user/install
# redis++
RUN git clone https://github.com/sewenew/redis-plus-plus.git &&\
    cd redis-plus-plus && mkdir build && cd build && cmake .. && make install -j
# gtest
RUN wget https://github.com/google/googletest/archive/refs/tags/v1.14.0.tar.gz -O googletest-1.14.0.tar.gz &&\
    tar zxf googletest-1.14.0.tar.gz && cd googletest-1.14.0 && mkdir build && cd build &&\
    cmake .. && make install -j
# MLNX_OFED
RUN wget https://content.mellanox.com/ofed/MLNX_OFED-4.9-5.1.0.0/MLNX_OFED_LINUX-4.9-5.1.0.0-ubuntu20.04-x86_64.tgz -O ofed.tgz &&\
    tar zxf ofed.tgz && mv MLNX* ofed && cd ofed &&\
    ./mlnxofedinstall --force

USER user
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended &&\
    echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/usr/local/lib" >> ~/.zshrc &&\
    echo "ulimit -n unlimited" >> ~/.zshrc

# RUN curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
# echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/redis.list




# RUN wget https://repo.anaconda.com/archive/Anaconda3-2022.05-Linux-x86_64.sh -O anaconda-install.sh
# # install anaconda
# RUN chmod +x anaconda-install.sh && ./anaconda-install.sh -b &&\
#     echo PATH=$PATH:$HOME/anaconda3/bin >> $HOME/.bashrc && source ~/.bashrc\
#     conda init bash && source ~/.bashrc && conda activate base







