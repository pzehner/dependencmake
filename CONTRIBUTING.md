# Contributing

## Install development dependencies

Extra dependencies are used for development:

```sh
pip install ".[dev]"
```

## Tests

### Unit tests

Unit tests are managed by [`pytest`](https://docs.pytest.org/en/stable/).
You simpy run them with:

```sh
pytest
```

To also get code [coverage](https://coverage.readthedocs.io/en/stable/):

```sh
coverage run -m pytest
coverage report
```

### Static tests

Code can be statically analyzed with [`mypy`](http://mypy-lang.org/):

```sh
mypy .
```

## Code style

The source code follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) guidelines and is linted using [Black](https://black.readthedocs.io/en/stable/):

```sh
black .
```

PEP8 validity can be checked with [`flake8`](https://flake8.pycqa.org/en/latest/):

```sh
flake8
```

## Hooks

The project uses [`pre-commit`](https://pre-commit.com/) to manage pre-commit hooks.
Install them with:

```sh
pre-commit install
```

## Changelog

The project uses [`changelog-cli`](https://github.com/mc706/changelog-cli).
Each time a PR adds, changes, removes features or fixes a bug, the changelog should be updated with this tool:

```sh
changelog (new|change|breaks|fix) "<message>"
```

## Release process

1. Update changelog:
   ```sh
   changelog release
   ```
   It should suggest a major/minor/patch release depending on the content of the changelog.
