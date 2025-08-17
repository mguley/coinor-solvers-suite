## COIN-OR Optimization Solvers Docker Suite

A comprehensive Docker image containing the complete COIN-OR (Computational Infrastructure for Operations Research) optimization solver suite, built from source for maximum compatibility and performance.

#### Overview

This project provides a Docker image with five major COIN-OR optimization solvers, all compiled from source on Ubuntu 18.04 LTS with careful attention to dependencies and compatibility.
The image serves as a complete optimization toolkit for researchers, engineers, and data scientists working on various optimization problems.

#### Included Solvers

The Docker image includes the following optimization solvers:

#### 1. **CLP (v1.16.9)** - COIN-OR Linear Programming Solver
CLP is an open-source linear programming solver written in C++. 
It's designed to solve large-scale linear programming problems efficiently using both simplex and interior point methods. 
CLP is particularly known for its reliability and speed in solving linear optimization problems that arise in operations research and industrial applications.

#### 2. **Ipopt (v3.12.4)** - Interior Point Optimizer
Ipopt is a software package for large-scale nonlinear optimization. 
It implements an interior-point line-search filter method that can handle problems with thousands or even millions of variables and constraints.
Ipopt is widely used in engineering design, trajectory optimization, and parameter estimation problems.

#### 3. **CBC (v2.9.7)** - COIN-OR Branch and Cut
CBC is an open-source mixed integer linear programming solver. 
It uses branch-and-cut algorithms to solve mixed integer programming problems, making it suitable for combinatorial optimization, scheduling, routing, and resource allocation problems.
CBC builds upon CLP for its linear programming relaxations.

#### 4. **Bonmin (v1.8.4)** - Basic Open-source Nonlinear Mixed Integer Programming
Bonmin is designed to solve mixed-integer nonlinear programming (MINLP) problems. 
It combines the robustness of CBC for handling integer variables with the power of Ipopt for nonlinear optimization. 
This makes it ideal for problems in chemical engineering, energy systems, and logistics where both discrete decisions and nonlinear relationships are present.

#### 5. **Couenne (v0.5.7)** - Convex Over and Under ENvelopes for Nonlinear Estimation
Couenne is a global optimization solver for non-convex mixed-integer nonlinear programming problems. 
It implements a spatial branch-and-bound algorithm that guarantees finding the global optimum (within tolerance). 
Couenne is particularly valuable for problems where local optimization might miss the best solution, such as in molecular design and network optimization.

## Quick Start

#### Prerequisites

Before using this Docker image, ensure you have Docker installed on your system. 
You can download Docker from [https://www.docker.com/get-started](https://www.docker.com/get-started).

You'll also need the `MUMPS` archive file (`MUMPS_4.10.0.tar.gz`) placed in a `dist/` directory relative to the Dockerfile. 
This is required because the automatic download from the original source can be unreliable.

An additional resource from which we can try to download it: https://coin-or-tools.github.io/ThirdParty-Mumps

#### Building the Image

Clone this repository and build the Docker image:

```bash
git clone https://github.com/mguley/coinor-solvers-suite.git
cd coinor-solvers-suite

# Ensure you have the MUMPS archive in the dist/ directory
mkdir -p dist
# Place MUMPS_4.10.0.tar.gz in the dist/ directory

# Build the Docker image
docker compose up --build
```

The build process will take approximately 15-30 minutes depending on your system, as it compiles all solvers from source.

Once built, you can access the solvers:

```bash
docker exec -ti coinor_solvers bash

# Run a specific solver within the container
clp -help
ipopt -v
cbc -help
bonmin -help
couenne -v
```

#### Approach

The Docker image uses a multi-stage build process to optimize build time and final image size:

1. **Base Stage**: Sets up Ubuntu 18.04 with Python 3.8 and all necessary build dependencies
2. **Stage 1**: Builds CLP with MUMPS support for enhanced numerical stability
3. **Stage 2**: Builds Ipopt, leveraging the existing CLP installation
4. **Stage 3**: Builds CBC, which depends on CLP for LP relaxations
5. **Stage 4**: Builds Bonmin, integrating CBC and Ipopt capabilities
6. **Stage 5**: Builds Couenne for global optimization, building on all previous solvers

Each stage carefully manages dependencies to ensure compatibility and optimal performance. 
The use of Ubuntu 18.04 LTS provides a stable, well-tested foundation that's compatible with a wide range of systems.

#### Technical Details

`Build Environment`
- **Base OS**: Ubuntu 18.04 LTS
- **Python**: 3.8 (installed via deadsnakes PPA)
- **Compilers**: GCC 7, G++ 7, GFortran 7
- **Linear Algebra**: LAPACK, BLAS, ATLAS
- **Build System**: coinbrew with autotools

#### Fortran Compatibility
The image includes specific Fortran compiler flags (`-fallow-argument-mismatch -std=legacy`) to ensure compatibility with modern GFortran versions while building legacy Fortran code in the solver dependencies.

#### MUMPS Integration
MUMPS (Multifrontal Massively Parallel sparse direct Solver) is included as a local archive to ensure reliable builds. 
It provides robust sparse matrix factorization capabilities that enhance the numerical stability of the solvers.

#### License

This Docker configuration is provided under the MIT License. However, please note that each COIN-OR solver has its own license:

- **CLP**: Eclipse Public License 1.0
- **Ipopt**: Eclipse Public License 1.0
- **CBC**: Eclipse Public License 1.0
- **Bonmin**: Eclipse Public License 1.0
- **Couenne**: Eclipse Public License 1.0

Please refer to each solver's documentation for detailed license information.

#### Known Issues

1. **Build Time**: The complete build process takes 15-30 minutes due to compilation from source
2. **MUMPS Download**: The original MUMPS download source can be unreliable, which is why we include it locally

#### Resources

- [COIN-OR Official Website](https://www.coin-or.org/)
- [CLP Documentation](https://github.com/coin-or/Clp)
- [Ipopt Documentation](https://coin-or.github.io/Ipopt/)
- [CBC Documentation](https://github.com/coin-or/Cbc)
- [Bonmin Documentation](https://www.coin-or.org/Bonmin/)
- [Couenne Documentation](https://www.coin-or.org/Couenne/)

**Note**: This image is designed for research purposes.