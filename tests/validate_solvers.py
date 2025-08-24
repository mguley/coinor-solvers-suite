#!/usr/bin/env python3
"""
COIN-OR solvers validation suite
Tests each solver with appropriate optimization problems to ensure correct installation
"""

import os
import subprocess
import sys
from datetime import datetime
from importlib.metadata import version as _pkg_version, PackageNotFoundError

import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition


def print_header(text: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_subheader(text: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n--- {text} ---")


def print_success(text: str) -> None:
    """Print success message in green."""
    print(f"\033[92m✓ {text}\033[0m")


def print_failure(text: str) -> None:
    """Print failure message in red."""
    print(f"\033[91m✗ {text}\033[0m")


class SolverValidator:
    """Validates COIN-OR optimization solvers with appropriate test problems."""

    def __init__(self):
        self.solver_paths = {
            "clp": "/opt/coin-or/bin/clp",
            "cbc": "/opt/coin-or/bin/cbc",
            "ipopt": "/opt/coin-or/bin/ipopt",
            "bonmin": "/opt/coin-or/bin/bonmin",
            "couenne": "/opt/coin-or/bin/couenne",
        }
        self.test_results = {}

    def check_solver_binaries(self) -> bool:
        """Verify that solver binaries exist and are executable."""
        print_header("STEP 1: Checking solver binary files")
        all_found = True

        for solver_name, path in self.solver_paths.items():
            if os.path.exists(path):
                # Check if file is executable
                if os.access(path, os.X_OK):
                    print_success(f"{solver_name.upper()}: Found and executable at {path}")

                    # Try to get version info
                    try:
                        version_flags = {
                            "clp": ["-help"],
                            "cbc": ["-help"],
                            "ipopt": ["-v"],
                            "bonmin": ["-v"],
                            "couenne": ["-v"],
                        }

                        result = subprocess.run(
                            [path] + version_flags.get(solver_name, ["-v"]),
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        output = result.stdout or result.stderr
                        if output:
                            version_line = output.strip().split("\n")[0]
                            print(f"  Version info: {version_line[:80]}")
                    except Exception as e:
                        print_failure(f"{solver_name.upper()}: {e}")
                else:
                    print_failure(f"{solver_name.upper()}: Found but not executable at {path}")
                    all_found = False
            else:
                print_failure(f"{solver_name.upper()}: Not found at {path}")
                all_found = False

        return all_found

    def test_clp_solver(self) -> bool:
        """Test CLP with a simple Linear Programming problem."""
        print_subheader("Testing CLP (Linear Programming)")

        try:
            # Create a simple LP problem: maximize 3x + 2y
            # subject to: x + y <= 4, 2x + y <= 5, x >= 0, y >= 0
            model = pyo.ConcreteModel("CLP_Test")

            model.x = pyo.Var(bounds=(0, None))
            model.y = pyo.Var(bounds=(0, None))

            # Objective: maximize 3x + 2y
            model.obj = pyo.Objective(
                expr=3 * model.x + 2 * model.y,
                sense=pyo.maximize
            )

            # Constraints
            model.con1 = pyo.Constraint(expr=model.x + model.y <= 4)
            model.con2 = pyo.Constraint(expr=2 * model.x + model.y <= 5)

            # Solve with CLP
            solver = SolverFactory('clp', executable=self.solver_paths['clp'])
            result = solver.solve(model, tee=False)

            # Check results
            if result.solver.status == SolverStatus.ok:
                if result.solver.termination_condition == TerminationCondition.optimal:
                    print_success("CLP solved successfully!")
                    print(f"    Optimal solution: x = {pyo.value(model.x):.4f}, y = {pyo.value(model.y):.4f}")
                    print(f"    Objective value = {pyo.value(model.obj):.4f}")
                    self.test_results['clp'] = True
                    return True
                else:
                    print_failure(f"CLP terminated with: {result.solver.termination_condition}")
            else:
                print_failure(f"CLP solver status: {result.solver.status}")
        except Exception as e:
            print_failure(f"CLP test failed with error: {str(e)}")

        self.test_results['clp'] = False
        return False

    def test_cbc_solver(self) -> bool:
        """Test CBC with a Mixed-Integer Linear Programming problem."""
        print_subheader("Testing CBC (Mixed-Integer Linear Programming)")

        try:
            # Create a simple MILP: knapsack problem
            model = pyo.ConcreteModel("CBC_Test")

            # Data for knapsack problem
            items = ['item1', 'item2', 'item3']
            value = {'item1': 10, 'item2': 20, 'item3': 15}
            weight = {'item1': 5, 'item2': 10, 'item3': 7}
            capacity = 15

            # Binary variables: 1 if item is selected, 0 otherwise
            model.x = pyo.Var(items, domain=pyo.Binary)

            # Objective: maximize total value
            model.obj = pyo.Objective(
                expr=sum(value[i] * model.x[i] for i in items),
                sense=pyo.maximize
            )

            # Constraint: total weight <= capacity
            model.weight_constraint = pyo.Constraint(
                expr=sum(weight[i] * model.x[i] for i in items) <= capacity
            )

            # Solve with CBC
            solver = SolverFactory('cbc', executable=self.solver_paths['cbc'])
            result = solver.solve(model, tee=False)

            # Check results
            if result.solver.status == SolverStatus.ok:
                if result.solver.termination_condition == TerminationCondition.optimal:
                    print_success("CBC solved successfully!")
                    print(f"    Selected items: ", end="")
                    for i in items:
                        if pyo.value(model.x[i]) > 0.5:
                            print(f"{i} ", end="")
                    print(f"\n    Total value = {pyo.value(model.obj):.0f}")
                    self.test_results['cbc'] = True
                    return True
                else:
                    print_failure(f"CBC terminated with: {result.solver.termination_condition}")
            else:
                print_failure(f"CBC solver status: {result.solver.status}")
        except Exception as e:
            print_failure(f"CBC test failed with error: {str(e)}")

        self.test_results['cbc'] = False
        return False

    def test_ipopt_solver(self) -> bool:
        """Test Ipopt with a Nonlinear Programming problem."""
        print_subheader("Testing Ipopt (Nonlinear Programming)")

        try:
            # Create a simple NLP: minimize (x-2)^2 + (y-3)^2
            # subject to: x^2 + y^2 <= 25
            model = pyo.ConcreteModel("Ipopt_Test")

            # Variables with initial values
            model.x = pyo.Var(initialize=1.0)
            model.y = pyo.Var(initialize=1.0)

            # Objective: minimize distance from point (2,3)
            model.obj = pyo.Objective(
                expr=(model.x - 2) ** 2 + (model.y - 3) ** 2,
                sense=pyo.minimize
            )

            # Nonlinear constraint: must be within circle of radius 5
            model.circle_constraint = pyo.Constraint(
                expr=model.x ** 2 + model.y ** 2 <= 25
            )

            # Solve with Ipopt
            solver = SolverFactory('ipopt', executable=self.solver_paths['ipopt'])
            solver.options['max_iter'] = 1000

            result = solver.solve(model, tee=False)

            # Check results
            if result.solver.status == SolverStatus.ok:
                if result.solver.termination_condition == TerminationCondition.optimal:
                    print_success("Ipopt solved successfully!")
                    print(f"    Optimal solution: x = {pyo.value(model.x):.4f}, y = {pyo.value(model.y):.4f}")
                    print(f"    Objective value = {pyo.value(model.obj):.4f}")
                    self.test_results['ipopt'] = True
                    return True
                else:
                    print_failure(f"Ipopt terminated with: {result.solver.termination_condition}")
            else:
                print_failure(f"Ipopt solver status: {result.solver.status}")
        except Exception as e:
            print_failure(f"Ipopt test failed with error: {str(e)}")

        self.test_results['ipopt'] = False
        return False

    def test_bonmin_solver(self) -> bool:
        """Test Bonmin with a Mixed-Integer Nonlinear Programming problem."""
        print_subheader("Testing Bonmin (Mixed-Integer Nonlinear Programming)")

        try:
            # Create a simple MINLP: facility location with nonlinear costs
            model = pyo.ConcreteModel("Bonmin_Test")

            # Binary variable: whether to open facility
            model.open = pyo.Var(domain=pyo.Binary, initialize=1)

            # Continuous variable: production level
            model.production = pyo.Var(bounds=(0, 10), initialize=5)

            # Objective: minimize fixed cost + nonlinear production cost
            model.obj = pyo.Objective(
                expr=100 * model.open + model.production ** 2,
                sense=pyo.minimize
            )

            # Constraints
            model.production_limit = pyo.Constraint(
                expr=model.production <= 10 * model.open
            )

            model.min_production = pyo.Constraint(
                expr=model.production >= 3 * model.open
            )

            # Solve with Bonmin
            solver = SolverFactory('bonmin', executable=self.solver_paths['bonmin'])
            solver.options['bonmin.algorithm'] = 'B-BB'

            result = solver.solve(model, tee=False)

            # Check results
            if result.solver.status == SolverStatus.ok:
                if result.solver.termination_condition in [
                    TerminationCondition.optimal,
                    TerminationCondition.locallyOptimal,
                ]:
                    print_success("Bonmin solved successfully!")
                    print(f"    Facility open: {'Yes' if pyo.value(model.open) > 0.5 else 'No'}")
                    print(f"    Production level: {pyo.value(model.production):.4f}")
                    print(f"    Total cost = {pyo.value(model.obj):.4f}")
                    self.test_results['bonmin'] = True
                    return True
                else:
                    print_failure(f"Bonmin terminated with: {result.solver.termination_condition}")
            else:
                print_failure(f"Bonmin solver status: {result.solver.status}")
        except Exception as e:
            print_failure(f"Bonmin test failed with error: {str(e)}")

        self.test_results['bonmin'] = False
        return False

    def test_couenne_solver(self) -> bool:
        """Test Couenne with a non-convex MINLP problem."""
        print_subheader("Testing Couenne (Global Optimization)")

        try:
            # Create a non-convex MINLP with potential local minima
            model = pyo.ConcreteModel("Couenne_Test")

            # Mixed variables
            model.x = pyo.Var(bounds=(0, 5), initialize=1)
            model.y = pyo.Var(within=pyo.Integers, bounds=(0, 3), initialize=1)

            # Non-convex objective with multiple local minima
            model.obj = pyo.Objective(
                expr=pyo.sin(model.x) * model.x + model.y ** 2 - 2 * model.y,
                sense=pyo.minimize
            )

            # Nonlinear constraint
            model.constraint = pyo.Constraint(expr=model.x ** 2 + model.y <= 8)

            # Solve with Couenne
            solver = SolverFactory('couenne', executable=self.solver_paths['couenne'])

            result = solver.solve(model, tee=False)

            # Check results
            if result.solver.status == SolverStatus.ok:
                if result.solver.termination_condition in [
                    TerminationCondition.optimal,
                    TerminationCondition.globallyOptimal,
                ]:
                    print_success("Couenne solved successfully!")
                    print(f"    Global optimum: x = {pyo.value(model.x):.4f}, y = {pyo.value(model.y):.0f}")
                    print(f"    Objective value = {pyo.value(model.obj):.4f}")
                    self.test_results['couenne'] = True
                    return True
                else:
                    print_failure(f"Couenne terminated with: {result.solver.termination_condition}")
            else:
                print_failure(f"Couenne solver status: {result.solver.status}")
        except Exception as e:
            print_failure(f"Couenne test failed with error: {str(e)}")

        self.test_results['couenne'] = False
        return False

    def run_all_tests(self) -> int:
        """Execute all solver validation tests and return exit code."""
        print_header("COIN-OR SOLVERS VALIDATION SUITE")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python version: {sys.version}")
        try:
            print(f"Pyomo version: {_pkg_version('pyomo')}")
        except PackageNotFoundError:
            print("Pyomo version: unknown")

        # Check binaries first
        binaries_ok = self.check_solver_binaries()
        if not binaries_ok:
            print_failure("Some solver binaries are missing!")
            return 1

        # Run tests
        print_header("STEP 2: Testing Solvers with Optimization Problems")

        self.test_clp_solver()
        self.test_cbc_solver()
        self.test_ipopt_solver()
        self.test_bonmin_solver()
        self.test_couenne_solver()

        # Summary
        print_header("TEST SUMMARY")
        all_passed = True
        for solver, passed in self.test_results.items():
            if passed:
                print_success(f"{solver.upper()}: PASSED")
            else:
                print_failure(f"{solver.upper()}: FAILED")
                all_passed = False

        print("")
        if all_passed:
            print_success("All solvers validated successfully!")
            return 0
        else:
            print_failure("Some solvers failed validation!")
            return 1


def test_single_solver(solver_name: str) -> int:
    """Test a single solver and return exit code."""
    validator = SolverValidator()

    print_header(f"Testing {solver_name.upper()} Solver")

    # Check if binary exists
    if solver_name not in validator.solver_paths:
        print_failure(f"Unknown solver: {solver_name}")
        return 1

    # Test the specific solver
    test_methods = {
        'clp': validator.test_clp_solver,
        'cbc': validator.test_cbc_solver,
        'ipopt': validator.test_ipopt_solver,
        'bonmin': validator.test_bonmin_solver,
        'couenne': validator.test_couenne_solver,
    }

    if solver_name in test_methods:
        success = test_methods[solver_name]()
        if success:
            print_success(f"{solver_name.upper()} validation PASSED!")
            return 0
        else:
            print_failure(f"{solver_name.upper()} validation FAILED!")
            return 1
    else:
        print_failure(f"No test available for {solver_name}")
        return 1


def main() -> int:
    """Main entry point for the validation script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate COIN-OR optimization solvers'
    )
    parser.add_argument(
        '--solver',
        choices=['clp', 'cbc', 'ipopt', 'bonmin', 'couenne'],
        help='Test a specific solver instead of all solvers'
    )

    args = parser.parse_args()

    if args.solver:
        # Test single solver
        return test_single_solver(args.solver)
    else:
        # Test all solvers
        validator = SolverValidator()
        return validator.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())