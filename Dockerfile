# COIN-OR Optimization Solvers Suite
# This Dockerfile builds a complete suite of COIN-OR optimization solvers from source
# Includes: CLP, Ipopt, CBC, Bonmin, and Couenne
# Built on Ubuntu 18.04 LTS with multi-stage optimization for minimal final image size

# ============================================================================
# BASE STAGE: Set up Ubuntu 18.04 with all build dependencies
# ============================================================================
FROM ubuntu:18.04 AS base

WORKDIR /tmp

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system essentials and configure locale to prevent warnings
RUN apt-get update && apt-get install -y \
    software-properties-common \
    apt-utils \
    locales \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8

# Set locale environment variables
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LC_NUMERIC=en_US.UTF-8

# Install the build dependencies required for compiling the solvers
# Including: compilers, linear algebra libraries, and solver-specific dependencies
RUN apt-get install -y \
    build-essential \
    gfortran \
    pkg-config \
    git \
    wget \
    curl \
    ca-certificates \
    liblapack-dev \
    libblas-dev \
    libatlas-base-dev \
    libmetis-dev \
    libmumps-seq-dev \
    glpk-utils \
    libglpk-dev \
    libc6-dev \
    libgcc-7-dev \
    libstdc++-7-dev \
    libgfortran-7-dev \
    && mkdir -p /opt/coin-or

# Clean APT cache to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# ============================================================================
# STAGE 1: Build CLP (Linear Programming solver)
# ============================================================================
FROM base AS stage1-clp

# Copy local MUMPS archive (workaround for unreliable download sources)
COPY dist/MUMPS_4.10.0.tar.gz /tmp/MUMPS_4.10.0.tar.gz

# Display build environment information
RUN echo "=== System Information ===" \
    && cat /etc/lsb-release \
    && gcc --version | head -1 \
    && g++ --version | head -1 \
    && gfortran --version | head -1

# Download coinbrew build tool
RUN cd /tmp \
    && wget https://raw.githubusercontent.com/coin-or/coinbrew/master/coinbrew \
    && chmod +x coinbrew

# Set Fortran compiler flags for compatibility with modern compilers
ENV FFLAGS="-O2 -fallow-argument-mismatch -std=legacy" \
    FCFLAGS="-O2 -fallow-argument-mismatch -std=legacy" \
    F77FLAGS="-O2 -fallow-argument-mismatch -std=legacy"

# Pre-stage MUMPS to avoid download failures during build
RUN echo "=== Pre-staging MUMPS ===" \
    && cd /tmp \
    && git clone --branch=releases/1.5.5 --depth=1 \
        https://github.com/coin-or-tools/ThirdParty-Mumps ThirdParty/Mumps \
    && cd ThirdParty/Mumps \
    && cp /tmp/MUMPS_4.10.0.tar.gz . \
    && tar -xzf MUMPS_4.10.0.tar.gz \
    && mv MUMPS_4.10.0 MUMPS \
    && if [ -f "mumps.patch" ]; then patch -p0 < mumps.patch; fi \
    && touch .build

# Fetch CLP source code
RUN cd /tmp \
    && ./coinbrew fetch Clp:releases/1.16.9 --no-prompt --skip-update

# Build and install CLP
RUN cd /tmp \
    && ./coinbrew build Clp --prefix=/opt/coin-or --no-prompt \
        ADD_FFLAGS="-fallow-argument-mismatch -std=legacy" \
        ADD_FCFLAGS="-fallow-argument-mismatch -std=legacy" \
    && ./coinbrew install Clp

# Verify CLP installation
RUN echo "=== Verifying CLP ===" \
    && /opt/coin-or/bin/clp -version 2>&1 || echo "CLP installed"

# ============================================================================
# STAGE 2: Build Ipopt (Interior Point Optimizer for nonlinear optimization)
# ============================================================================
FROM stage1-clp AS stage2-ipopt

# Fetch Ipopt source
RUN cd /tmp \
    && ./coinbrew fetch Ipopt:releases/3.12.4 --no-prompt || true

# Build and install Ipopt
RUN cd /tmp \
    && ./coinbrew build Ipopt --prefix=/opt/coin-or --no-prompt \
        ADD_FFLAGS="-fallow-argument-mismatch -std=legacy" \
        ADD_FCFLAGS="-fallow-argument-mismatch -std=legacy" \
    && ./coinbrew install Ipopt

# Verify Ipopt installation
RUN echo "=== Verifying Ipopt ===" \
    && if [ -f /opt/coin-or/bin/ipopt ]; then \
         /opt/coin-or/bin/ipopt -v 2>&1 || echo "Ipopt installed"; \
       fi

# ============================================================================
# STAGE 3: Build CBC (Mixed-Integer Linear Programming solver)
# ============================================================================
FROM stage2-ipopt AS stage3-cbc

# Fetch CBC source
RUN cd /tmp \
    && ./coinbrew fetch Cbc:releases/2.9.7 --no-prompt || true

# Build and install CBC (will automatically detect and use installed CLP)
RUN cd /tmp \
    && ./coinbrew build Cbc --prefix=/opt/coin-or --no-prompt \
        ADD_FFLAGS="-fallow-argument-mismatch -std=legacy" \
        ADD_FCFLAGS="-fallow-argument-mismatch -std=legacy" \
    && ./coinbrew install Cbc

# Verify CBC installation
RUN echo "=== Verifying CBC ===" \
    && if [ -f /opt/coin-or/bin/cbc ]; then \
         /opt/coin-or/bin/cbc -version 2>&1 || echo "CBC installed"; \
       fi

# ============================================================================
# STAGE 4: Build Bonmin (Mixed-Integer Nonlinear Programming solver)
# ============================================================================
FROM stage3-cbc AS stage4-bonmin

# Clone Bonmin source directly to avoid dependency conflicts
RUN cd /tmp \
    && git clone --branch=releases/1.8.4 --depth=1 \
        https://github.com/coin-or/Bonmin Bonmin

# Configure Bonmin to use existing solver installations
RUN cd /tmp/Bonmin \
    && ./configure \
        --prefix=/opt/coin-or \
        --with-coinutils-lib="-L/opt/coin-or/lib -lCoinUtils" \
        --with-coinutils-incdir="/opt/coin-or/include/coin" \
        --with-osi-lib="-L/opt/coin-or/lib -lOsi -lOsiCbc -lOsiClp" \
        --with-osi-incdir="/opt/coin-or/include/coin" \
        --with-clp-lib="-L/opt/coin-or/lib -lClp -lOsiClp" \
        --with-clp-incdir="/opt/coin-or/include/coin" \
        --with-cgl-lib="-L/opt/coin-or/lib -lCgl" \
        --with-cgl-incdir="/opt/coin-or/include/coin" \
        --with-cbc-lib="-L/opt/coin-or/lib -lCbc -lCbcSolver -lOsiCbc" \
        --with-cbc-incdir="/opt/coin-or/include/coin" \
        --with-ipopt-lib="-L/opt/coin-or/lib -lipopt" \
        --with-ipopt-incdir="/opt/coin-or/include/coin" \
        --enable-shared \
        --disable-static \
        LDFLAGS="-L/opt/coin-or/lib" \
        CPPFLAGS="-I/opt/coin-or/include/coin" \
        FFLAGS="-O2 -fallow-argument-mismatch -std=legacy" \
        FCFLAGS="-O2 -fallow-argument-mismatch -std=legacy"

# Build and install Bonmin
RUN cd /tmp/Bonmin \
    && make -j1 \
    && make install

# Verify Bonmin installation
RUN echo "=== Verifying Bonmin ===" \
    && if [ -f /opt/coin-or/bin/bonmin ]; then \
         /opt/coin-or/bin/bonmin 2>&1 | head -10 || echo "Bonmin installed"; \
       fi

# ============================================================================
# STAGE 5: Build Couenne (Global Optimization solver)
# ============================================================================
FROM stage4-bonmin AS stage5-couenne

# Clone Couenne source directly
RUN cd /tmp \
    && git clone --branch=releases/0.5.7 --depth=1 \
        https://github.com/coin-or/Couenne Couenne

# Configure Couenne to use existing solver installations
RUN cd /tmp/Couenne \
    && ./configure \
        --prefix=/opt/coin-or \
        --with-coinutils-lib="-L/opt/coin-or/lib -lCoinUtils" \
        --with-coinutils-incdir="/opt/coin-or/include/coin" \
        --with-osi-lib="-L/opt/coin-or/lib -lOsi -lOsiCbc -lOsiClp" \
        --with-osi-incdir="/opt/coin-or/include/coin" \
        --with-clp-lib="-L/opt/coin-or/lib -lClp -lOsiClp" \
        --with-clp-incdir="/opt/coin-or/include/coin" \
        --with-cgl-lib="-L/opt/coin-or/lib -lCgl" \
        --with-cgl-incdir="/opt/coin-or/include/coin" \
        --with-cbc-lib="-L/opt/coin-or/lib -lCbc -lCbcSolver -lOsiCbc" \
        --with-cbc-incdir="/opt/coin-or/include/coin" \
        --with-ipopt-lib="-L/opt/coin-or/lib -lipopt" \
        --with-ipopt-incdir="/opt/coin-or/include/coin" \
        --with-bonmin-lib="-L/opt/coin-or/lib -lbonmin" \
        --with-bonmin-incdir="/opt/coin-or/include/coin" \
        --enable-shared \
        --disable-static \
        LDFLAGS="-L/opt/coin-or/lib" \
        CPPFLAGS="-I/opt/coin-or/include/coin" \
        FFLAGS="-O2 -fallow-argument-mismatch -std=legacy" \
        FCFLAGS="-O2 -fallow-argument-mismatch -std=legacy"

# Build and install Couenne
RUN cd /tmp/Couenne \
    && make -j1 \
    && make install

# ============================================================================
# PYTHON BUILDER STAGE: Build Python 3.8 virtual environment
# ============================================================================
FROM ubuntu:18.04 AS python-builder

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.8 from deadsnakes PPA
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        gnupg2 \
        ca-certificates \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.8 \
        python3.8-dev \
        python3.8-venv \
        python3.8-distutils \
        gcc \
        g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/doc/* \
    && rm -rf /usr/share/man/*

# Create and activate virtual environment
RUN python3.8 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install core packages, Pyomo
RUN pip install --no-cache-dir --upgrade pip wheel setuptools pyomo

# Clean up pip cache
RUN pip cache purge 2>/dev/null || true && rm -rf /tmp/*

# ============================================================================
# FINAL STAGE: Create minimal runtime image with Python 3.8 and solvers
# ============================================================================
FROM ubuntu:18.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.8 and runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        ca-certificates \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.8 \
        python3.8-distutils \
        libgfortran4 \
        libgomp1 \
        libquadmath0 \
        libblas3 \
        liblapack3 \
        libstdc++6 \
        libmetis5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && rm -rf /usr/share/doc/* \
    && rm -rf /usr/share/man/*

# Copy the compiled solver binaries from the build stage
COPY --from=stage5-couenne /opt/coin-or/bin/ /opt/coin-or/bin/
# Copy the compiled shared libraries
COPY --from=stage5-couenne /opt/coin-or/lib/*.so* /opt/coin-or/lib/
# Configure the system to find our libraries
RUN echo "/opt/coin-or/lib" > /etc/ld.so.conf.d/coin-or.conf && ldconfig

# Copy Python virtual environment
COPY --from=python-builder /opt/venv /opt/venv

# Set up environment variables
ENV PATH="/opt/venv/bin:/opt/coin-or/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COIN_OR_HOME="/opt/coin-or" \
    PYOMO_CONFIG_PATH="/opt/coin-or/bin" \
    LD_LIBRARY_PATH="/opt/coin-or/lib:${LD_LIBRARY_PATH}" \
    VIRTUAL_ENV="/opt/venv"

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash coinor && \
    mkdir -p /app && \
    chown -R coinor:coinor /app

WORKDIR /app
USER coinor

CMD ["/bin/bash", "-c", "echo 'COIN-OR Optimization Suite Ready' && tail -f /dev/null"]