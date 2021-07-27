# Contributing

## Install development dependencies

Extra dependencies are used for development:

```sh
poetry install
```

## Tests

### Unit tests

Unit tests are managed by [`pytest`](https://docs.pytest.org/en/stable/).
You simpy run them with:

```sh
poetry run pytest
```

This gives code coverage automatically.

### Static tests

Code can be statically analyzed with [`mypy`](http://mypy-lang.org/):

```sh
poetry run mypy .
```

## Code style

The source code follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) guidelines and is linted using [Black](https://black.readthedocs.io/en/stable/):

```sh
poetry run black .
```

PEP8 validity can be checked with [`flake8`](https://flake8.pycqa.org/en/latest/):

```sh
poetry run flake8
```

## Hooks

The project uses [`pre-commit`](https://pre-commit.com/) to manage pre-commit hooks.
Install them with:

```sh
poetry run pre-commit install
```

## Changelog

The project uses [`changelog-cli`](https://github.com/mc706/changelog-cli).
Each time a PR adds, changes, removes features or fixes a bug, the changelog should be updated with this tool:

```sh
poetry run changelog (new|change|breaks|fix) "<message>"
```

## Version

Version is stored in `src/dependencmake/version.py:__version__` and in `pyproject.toml`, it respects [semantic versionning](https://semver.org).
It is bumped with [`bump2version`](https://github.com/c4urself/bump2version):

```sh
poetry run bumpversion (major|minor|patch)
```

## Release process

1. Checkout to the `develop` branch and pull:
   ```sh
   git checkout develop
   git pull
   ```
   Check if there are any cosmetic changes to make;
2. Update changelog:
   ```sh
   poetry run changelog release
   git add CHANGELOG.md
   git commit -n -m "Update CHANGELOG for release"
   ```
   It should suggest a major/minor/patch release depending on the content of the changelog.
   You can also manually specify the desired version with `--patch`, `--minor`, `--major`;
3. Update license to have correct year for release:
   ```sh
   bash ./update_license.sh
   git add LICENSE
   git commit -n -m "Update LICENSE for release"
   ```
4. Bump version to obtain **the same version** as in changelog:
   ```sh
   poetry run bumpversion (major|minor|patch)
   ```
   It commits and creates the Git tag automatically;
5. Push the changes to the server, with the tag:
   ```sh
   git push
   git push origin <tag>
   ```
6. Checkout to the `master` branch, pull, merge the tagged commit previously created, then push:
   ```sh
   git checkout master
   git pull
   git merge <tag>
   git push
   ```
7. Create the distribution files and publish them:
   ```sh
   poetry publish --build
   ```
8. On Github, draft a new release, set the version number with the created tag ("Existing tag" should be read).
    Set the release title with "Version <tag>" and copy-paste the corresponding section of the changelog file in the release description.
