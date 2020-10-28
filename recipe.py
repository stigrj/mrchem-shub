#!/usr/bin/env python

"""
HPCCM recipe for MRChem Singularity image

Contents:
  Ubuntu 18.04
  GNU compilers (upstream)

Optional MPI content:
  OpenMPI
  OFED/MOFED
  PMI2 (SLURM)
  UCX

Generating recipe:
  1. MRChem vX.Y.Z with no MPI support (only OpenMP)
     $ ./recipe.py --mrchem=X.Y.Z > Singularity.vX.Y.Z-nompi
     $ singularity build mrchem-vX.Y.Z-nompi.sif Singularity.vX.Y.Z-nompi

  1. MRChem vX.Y.Z with OpenMPI vA.B.C and Mellanox OFED drivers
     $ ./recipe.py --mrchem=X.Y.Z --openmpi=A.B.C --mofed > Singularity.vX.Y.Z-openmpiA.B.C
     $ singularity build mrchem-vX.Y.Z-openmpiA.B.C.sif Singularity.vX.Y.Z-nompi

Running with Singularity:
  1. Using a compatible host MPI runtime
     $ singularity run mrchem-fram.sif mrchem --dryrun molecule.inp
     $ mpirun -map-by ppr:1:numa -bind-to numa singularity run mrchem-fram.sif mrchem.x molecule.json >molecule.out

  2. Using SLURM srun
     $ singularity run mrchem-fram.sif mrchem --dryrun molecule.inp
     $ srun singularity run mrchem-fram.sif mrchem.x molecule.json >molecule.out
"""

import argparse
import hpccm

### Parse command line arguments
parser = argparse.ArgumentParser(description='HPCCM recipe for MRChem')
parser.add_argument(
    "--mrchem",
    action="store",
    type=str,
    dest="mrchem_version",
    help="MRChem version",
)
parser.add_argument(
    "--openmpi",
    action="store",
    type=str,
    dest="openmpi_version",
    help="OpenMPI version",
)
parser.add_argument(
    "--mofed",
    action="store_true",
    dest="mofed",
    default=False,
    help="Build with Mellanox OFED drivers",
)
args = parser.parse_args()

# CentOS base image
Stage0 = hpccm.Stage()
Stage0 += hpccm.primitives.baseimage(image='ubuntu:18.04', _as='build')

# GNU compilers
compiler = hpccm.building_blocks.gnu()
Stage0 += compiler

enable_mpi="OFF"
cxx_compiler="g++"
if args.openmpi_version:
    enable_mpi="ON"
    cxx_compiler="mpicxx"
    # (M)OFED
    if args.mofed:
        Stage0 += hpccm.building_blocks.mlnx_ofed()
    else:
        Stage0 += hpccm.building_blocks.ofed()

    # UCX
    Stage0 += hpccm.building_blocks.ucx(cuda=False, ofed=True)

    # PMI2
    Stage0 += hpccm.building_blocks.slurm_pmi2()

    # OpenMPI (use UCX instead of IB directly)
    Stage0 += hpccm.building_blocks.openmpi(cuda=False,
                                            infiniband=False,
                                            pmi='/usr/local/slurm-pmi2',
                                            ucx='/usr/local/ucx',
                                            toolchain=compiler.toolchain,
                                            version=args.openmpi_version)

# CMake
Stage0 += hpccm.building_blocks.cmake(eula=True, version='3.16.3')

# Python 3
Stage0 += hpccm.building_blocks.python(python2=False, python3=True)

# MRChem
Stage0 += hpccm.building_blocks.packages(apt=['patch'])
Stage0 += hpccm.building_blocks.generic_cmake(cmake_opts=['-D CMAKE_BUILD_TYPE=Release',
                                                          '-D ENABLE_MPI={}'.format(enable_mpi),
                                                          '-D ENABLE_OPENMP=ON',
                                                          '-D ENABLE_ARCH_FLAGS=OFF',
                                                          '-D CXX_COMPILER={}'.format(cxx_compiler)],
                                              prefix='/usr/local/mrchem',
                                              url='http://github.com/MRChemSoft/mrchem/archive/v{}.tar.gz'.format(args.mrchem_version),
                                              directory='mrchem-{}'.format(args.mrchem_version))

Stage0 += hpccm.primitives.environment(variables={'PATH': '$PATH:/usr/local/mrchem/bin'})

### Set container specification output format
hpccm.config.set_container_format('singularity')

### Output container specification
print(Stage0)

# Runtime distributable stage
#Stage1 += baseimage(image='ubuntu:18.04')
#Stage1 += Stage0.runtime()
