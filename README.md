# DependenCmake

Yet another dependency manager for projects using CMake.

## Install

Install from downloaded repository with:

```sh
pip install .
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

More info on the accepted parameters in the configuration file section.

The program accepts several actions:

- `list` to list dependencies collected in the configuration file;
- `fetch` to fetch dependencies on local disk.


