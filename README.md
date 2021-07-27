[![Build Status](https://travis-ci.com/pzehner/dependencmake.svg?branch=master)](https://travis-ci.com/pzehner/dependencmake)
[![codecov](https://codecov.io/gh/pzehner/dependencmake/branch/master/graph/badge.svg?token=XE5V2XO9XM)](https://codecov.io/gh/pzehner/dependencmake)

# DependenCmake

Yet another dependency manager for projects using [CMake](https://cmake.org).

According to CMake [documentation](https://cmake.org/cmake/help/git-stage/guide/using-dependencies/index.html), the best way to consume a CMake dependency is to install it and find it.
Using includes just creates mess.

This helper can fetch, build and install CMake dependencies in a specific directory that you can add to your project with `-DCMAKE_PREFIX_PATH`.
It keeps your system environment clean as you won't mix libraries up.
This can be also convenient for Fortran projects where installing libraries is not the standard due to the volatility of `mod` files.

## Install

This package is managed with [Poetry](https://python-poetry.org/):

```sh
pip install poetry
```

Install from downloaded repository with:

```sh
poetry install --no-dev
```

## Usage

The generic usage of the command is:

```sh
ENV=value dependencmake action path/to/cmake/dir
```

which is pretty close to how CMake is called.
The program will fetch/build/install desired dependencies and stored the result of the different actions in a `dependencmake` directory in the current directory.

The program will look for a `dependencmake.yaml` file in the specified directory, where dependencies are listed:

```yaml
dependencies:
  - name: My dependency
    url: file://my_server/my_dep.zip
    cmake_args: -DUSE_MPI=ON
  - name: My other dependency
    url: http://my_repo/my_other_dep.git
    git_hash: 25481515
```

More info on the accepted parameters in the [configuration file](#configuration-file) section.

The program accepts several actions:

- `create-config` to create a new configuration file;
- `list` to list dependencies collected in the configuration file;
- `fetch` to fetch dependencies and copy them on local disk;
- `build` to fetch and build dependencies;
- `install` to fetch, build and install dependencies;
- `clean` to clean the cache.

The `build` and `install` actions will take any other arguments and pass them directly to CMake at configure step.

If you call `fetch`, `build` or `install` a second time, already fetched dependencies will most likely not be fetched again.
Git dependencies will be pulled (unless `git_no_update` is set) and other kind of dependencies will rest untouched.

Example of workflow:

```sh
mkdir build
cd build
dependencmake install .. -DCMAKE_BUILD_TYPE=Release
cmake .. -DCMAKE_PREFIX_PATH=$PWD/dependencmake/install -DCMAKE_BUILD_TYPE=Release
make
```

the `-DCMAKE_INSTALL_PREFIX` argument is required to tell CMake where dependencies are installed.

It is possible to set the install prefix to a custom value with the `install-prefix` argument.
In this case dependencies will be installed in this directory instead of in the DependenCmake cache:

```sh
mkdir build
cd build
dependencmake install --install-prefix lib/extern .. -DCMAKE_BUILD_TYPE=Release
cmake .. -DCMAKE_PREFIX_PATH=$PWD/lib/extern -DCMAKE_BUILD_TYPE=Release
make
```

## Configuration file

The configuration file uses the [YAML format](https://en.wikipedia.org/wiki/YAML).
It stores dependencies information in the `dependencies` key as a list.
Each item contains the following possible keys:

- `name`:
  Name of the dependency, used for display.
  Mandatory;
- `url`:
  URL where to get the dependency.
  Can be a Git repository, online only (must end by `.git`),
  an archive, online or local (must end by `.zip`, `.tar`, `.tar.bz2`, `.tbz2`, `.tar.gz`, `.tgz`, `.tar.xz` or `.txz`),
  or a plain directory, local only.
  Mandatory;
- `git_hash`:
  Git hash to checkout to in case of Git repository.
  The hash can be a commit hash or a tag.
  Optional;
- `git_no_update`:
  When set to `true`, if the Git repository has been cloned, it will not been pulled on another run.
  Optional;
- `cmake_subdir`:
  Subdirectory where to find the CMakeLists.txt file if it is not in the top directory.
  Optional;
- `cmake_args`:
  Specific arguments to pass to CMake at configuration time.
  Optional;
- `jobs`:
  Number of jobs to use when building the dependency.
  By default, number of CPU cores * 2 + 1.
  Optional.

## Cache

DependenCmake will put generated data in a `dependencmake` cache folder in the current working directory:

```
dependencmake/
+-- build/
+-- fetch/
+-- install/
```

It's pretty clear what the purpose of each subfolder of the cache is.
`fetch` and `build` both contain a subfolder for each dependency.
The dependency directory name is the lower case and slugified name of the dependency, appended with a MD5 hash of the URL.
This allows to make the directory unique per couple name/URL and humanly readable.
`install` has no logic enforced and is populated according to the `install` directives of the `CMakeLists.txt` files of the dependencies.

## Additionnal checks

After fetching dependencies, they are checked to detect patterns not managed by the program.
For now, diamond dependencies (where the same dependency is requested by two others) are invalid if they are not strictly equivalent.
