"""
MRChem OpenMPI-OFED image

Contents:
  Ubuntu 18.04
  GNU compilers (upstream)
  OFED
  OpenMPI
  PMI2 (SLURM)
  UCX

Building:
  1. Docker to Singularity
     $ hpccm --recipe mpi_bandwidth.py > Dockerfile
     $ sudo docker build -t mpi_bw -f Dockerfile .
     $ singularity build mpi_bw.sif docker-daemon://mpi_bw:latest

  2. Singularity
     $ hpccm --recipe mpi_bandwidth.py --format singularity --singularity-version=3.2 > Singularity.def
     $ sudo singularity build mpi_bw.sif Singularity.def

Running with Singularity:
  1. Using a compatible host MPI runtime
     $ singularity run mrchem-fram.sif mrchem --dryrun molecule.inp
     $ mpirun -map-by ppr:1:numa -bind-to numa singularity run mrchem-fram.sif mrchem.x molecule.json >molecule.out

  2. Using SLURM srun
     $ singularity run mrchem-fram.sif mrchem --dryrun molecule.inp
     $ srun singularity run mrchem-fram.sif mrchem.x molecule.json >molecule.out
"""

Stage0 += comment(__doc__, reformat=False)

# CentOS base image
Stage0 += baseimage(image='ubuntu:18.04', _as='build')

# GNU compilers
compiler = gnu()
Stage0 += compiler

# OFED
Stage0 += ofed()

# UCX
Stage0 += ucx(cuda=False, ofed=True, version='1.7.0')

# PMI2
Stage0 += slurm_pmi2()

# OpenMPI (use UCX instead of IB directly)
Stage0 += openmpi(cuda=False,
                  infiniband=False,
                  pmi='/usr/local/slurm-pmi2',
                  ucx='/usr/local/ucx',
                  toolchain=compiler.toolchain,
                  version='4.0.5')

# CMake
Stage0 += cmake(eula=True, version='3.16.3')

# Python 3
Stage0 += python(python2=False, python3=True)

# MRChem
mrchem_version="1.0.0"
Stage0 += packages(apt=['patch'])
Stage0 += generic_cmake(cmake_opts=['-D CMAKE_BUILD_TYPE=Release',
                                    '-D ENABLE_MPI=ON',
                                    '-D ENABLE_OPENMP=ON',
                                    '-D ENABLE_ARCH_FLAGS=OFF',
                                    '-D CXX_COMPILER=mpicxx'],
                        prefix='/usr/local/mrchem',
                        url='http://github.com/MRChemSoft/mrchem/archive/v{}.tar.gz'.format(mrchem_version),
                        directory='mrchem-{}'.format(mrchem_version))

Stage0 += environment(variables={'PATH': '$PATH:/usr/local/mrchem/bin'})

# Runtime distributable stage
#Stage1 += baseimage(image='ubuntu:18.04')
#Stage1 += Stage0.runtime()
