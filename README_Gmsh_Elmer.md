# Softwares to Install for Open-source simulation toolchain for Qiskit Metal
## Gmsh
- This is a design rendering and meshing software that we will be using to render our design and then divide it into fine elements (called a `mesh`), in order to solve the necessary differential equations (PDE's of Maxwell's Electromagnetic Laws). This is completely integrated with Qiskit Metal and is semi-automated.
- This will be automatically installed when you make a new `venv` environment and install qiskit metal using the instructions given above (except in Apple Silicon Macs, see the Note below).

### Test if Gmsh is properly installed
- Run the following in your terminal. A blank Gmsh window should open up. If it does, then hurray, you did it! 😄
```bash
$ gmsh
```

- Open a python REPL in your terminal and type `import gmsh` in the REPL. If `gmsh` gets imported without any errors, then it's installed properly with python.
```python
$ python
...
...
>>> import gmsh   # No Error
>>>
```

**NOTE:**
- On Apple Silicon Macs (with M1 and M2-series chips), installing Gmsh using `pip install gmsh` might not work for importing the package using python. Therefore, to successfully install Gmsh, and point it to the `gmsh` installed using `pip`, you need to install `gmsh` binary through [Homebrew](https://brew.sh/) as follows:
```bash
$ brew install gmsh
```
- Restart your terminal, activate the environment, and check if you're able to do `import gmsh` in a python REPL or a scratch jupyter notebook. If the import is successful, then congratulations, you've installed Gmsh successfully!

- **Note:** If the above steps still gives error in importing gmsh using `import gmsh` in your python environment, refer [this issue](https://gitlab.onelab.info/gmsh/gmsh/-/issues/1705), on the Gmsh GitLab repository, for more information. Also please feel free to contact us through the Qiskit Slack workspace on the `#metal` channel.

## ElmerFEM
- Congratulations on making it until here! Now we'll see how to install ElmerFEM.
- ElmerFEM is a Finite Element Method (FEM) solver that we'll be using to take the mesh generated by Gmsh, and the solve the Maxwell's equations on top of our meshed design. Right now, Qiskit Metal only supports capacitance-type simulations (Poisson equaiton solver provided by `StatElecSolver`) with ElmerFEM, so only LOM 2.0 analysis can be performed for tuning the qubits using the results obtained from ElmerFEM in the form of a Maxwell Capacitance matrix.
- ElmerFEM doesn't come as a python library and has different installation options on your operating system.
- Please follow the official guide provided by Elmer Foundation CSC, [here](https://github.com/ElmerCSC/elmerfem#elmer-fem)

**NOTE:** For Windows, please consider installing `ElmerFEM-gui-mpi-Windows-AMD64` and not `ElmerFEM-gui-nompi-Windows-AMD64` as it may not let ElmerGrid run on the input mesh from Gmsh. Refer [this issue](https://github.com/Qiskit/qiskit-metal/issues/933).

**NOTE:** For MacOS, please consider building the software from source rather than using Homebrew on Mac, as the homebrew install isn't very consistent and may cause issues in the future.

### After you complete your installation
- Add your installation path directory to your system's `PATH` environment variable (you can skip this on Windows and MacOS, as it is automatically done on those OS platforms during the installation steps).
- Restart your terminal.
- Check if ElmerFEM is installed successfully by checking installation for `ElmerGrid` and `ElmerSolver`.
- For testing ElmerGrid, type `ElmerGrid` in your terminal and if the PATH variable is set correctly, it should print a long output text. Check if you see the following at the end of the text:
```bash
$ ElmerGrid
Starting program Elmergrid
****************** Elmergrid ************************
This program can create simple 2D structured meshes consisting of
linear, quadratic or cubic rectangles or triangles. The meshes may
also be extruded and revolved to create 3D forms. In addition many
mesh formats may be imported into Elmer software. Some options have
not been properly tested. Contact the author if you face problems.

...
...
...

Thank you for using Elmergrid!
Send bug reports and feature wishes to elmeradm@csc.fi
```

- For testing ElmerSolver, type `ElmerSolver` in your terminal and if the PATH variable is set correctly, it should print a long output text. Check if you see the following:

```bash
$ ElmerSolver
ELMER SOLVER (v 9.0) STARTED AT: 2023/01/11 09:42:44
ParCommInit:  Initialize #PEs:            1
MAIN: OMP_NUM_THREADS not set. Using only 1 thread per task.
MAIN:
MAIN: =============================================================
MAIN: ElmerSolver finite element software, Welcome!
MAIN: This program is free software licensed under (L)GPL
MAIN: Copyright 1st April 1995 - , CSC - IT Center for Science Ltd.
MAIN: Webpage http://www.csc.fi/elmer, Email elmeradm@csc.fi
MAIN: Version: 9.0 (Rev: 02f61d697, Compiled: 2022-11-08)
MAIN:  Running one task without MPI parallelization.
MAIN:  Running with just one thread per task.
MAIN: =============================================================
ERROR:: ElmerSolver: Unable to find ELMERSOLVER_STARTINFO, can not execute.
Note: The following floating-point exceptions are signalling: IEEE_OVERFLOW_FLAG
STOP 1
```

If you see the above lines in the text in your terminal, then CONGRATULATIONS!!! You've successfully installed everything needed for using Gmsh and ElmerFEM with Qiskit Metal! 😄

**NOTE:** If you face issues at any of the steps above, feel free to contact us on #metal channel on Qiskit slack!!