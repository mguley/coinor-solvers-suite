## COIN-OR Optimization Solvers Docker Suite

![Build and Test](https://github.com/mguley/coinor-solvers-suite/workflows/Build%20and%20Test%20COIN-OR%20Solvers/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A comprehensive Docker image containing the complete COIN-OR (Computational Infrastructure for Operations Research) optimization solver suite, built from source with automated testing and validation.

#### Overview

This project provides a Docker image with five major COIN-OR optimization solvers, all compiled from source on Ubuntu 18.04 LTS.
The image includes automated validation testing through GitHub Actions, ensuring reliability and compatibility.
It serves as a complete optimization toolkit for researchers, engineers, and data scientists working on various optimization problems.

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

#### Using Docker Compose

The simplest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/mguley/coinor-solvers-suite.git
cd coinor-solvers-suite

# Build and start the container
docker compose up --build -d

# Access the container
docker exec -it coinor_solvers bash

# Run the validation suite to verify everything works
python /app/tests/validate_solvers.py
```

#### Using Docker directly

If you prefer to use Docker directly:

```bash
# Build the image
docker build -t coinor-suite:latest .

# Run the container
docker run -it --name coinor_solvers coinor-suite:latest bash

# Inside the container, test a solver
python -c "
import pyomo.environ as pyo
from pyomo.opt import SolverFactory

# Create a simple model
model = pyo.ConcreteModel()
model.x = pyo.Var(bounds=(0, 10))
model.obj = pyo.Objective(expr=model.x**2, sense=pyo.minimize)
model.con = pyo.Constraint(expr=model.x >= 2)

# Solve with Ipopt
solver = SolverFactory('ipopt', executable='/opt/coin-or/bin/ipopt')
result = solver.solve(model)
print(f'Solution: x = {pyo.value(model.x):.4f}')
"
```

#### Testing and validation

This project includes automated testing to ensure all solvers function correctly.

#### Running the validation suite

The project includes a Python validation script that tests each solver with appropriate optimization problems:

```bash
# Run all tests
docker exec coinor_solvers python /app/tests/validate_solvers.py

# Test a specific solver
docker exec coinor_solvers python /app/tests/validate_solvers.py --solver cbc
```

#### Python/Pyomo integration

The image comes pre-configured with Python 3.8 and Pyomo, making it easy to formulate and solve optimization problems:

```bash
# Inside the container
python -c "
import pyomo.environ as pyo
from pyomo.opt import SolverFactory

# Example: Portfolio Optimization with CBC
def solve_portfolio_optimization():
    model = pyo.ConcreteModel()
    
    # Define assets
    assets = ['Stock_A', 'Stock_B', 'Stock_C']
    returns = {'Stock_A': 0.10, 'Stock_B': 0.15, 'Stock_C': 0.12}
    risk = {'Stock_A': 0.05, 'Stock_B': 0.10, 'Stock_C': 0.07}
    
    # Decision variables: fraction to invest in each asset
    model.x = pyo.Var(assets, bounds=(0, 1))
    
    # Objective: Maximize return
    model.obj = pyo.Objective(
        expr=sum(returns[i] * model.x[i] for i in assets),
        sense=pyo.maximize
    )
    
    # Constraints
    model.budget = pyo.Constraint(expr=sum(model.x[i] for i in assets) == 1)
    model.risk_limit = pyo.Constraint(
        expr=sum(risk[i] * model.x[i] for i in assets) <= 0.08
    )
    
    # Solve with CBC
    solver = SolverFactory('cbc', executable='/opt/coin-or/bin/cbc')
    result = solver.solve(model, tee=True)
    
    return model
    
solve_portfolio_optimization()
"
```

The build process will take approximately 15-30 minutes depending on your system, as it compiles all solvers from source.

#### Approach

The Docker image uses a multi-stage build process to optimize build time and final image size:

1. Base stage: base dependencies (Ubuntu 18.04 + build tools)
2. Stage 1: CLP with MUMPS support
3. Stage 2: Ipopt (leveraging CLP)
4. Stage 3: CBC (using CLP for LP relaxations)
5. Stage 4: Bonmin (integrating CBC + Ipopt)
6. Stage 5: builds Couenne for global optimization (based on all previous solvers)
7. Python environment setup
8. Minimal runtime image

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
- [Ipopt Documentation](https://github.com/coin-or/Ipopt)
- [CBC Documentation](https://github.com/coin-or/Cbc)
- [Bonmin Documentation](https://github.com/coin-or/Bonmin)
- [Couenne Documentation](https://github.com/coin-or/Couenne)

**Note**: This image is designed for research purposes.
