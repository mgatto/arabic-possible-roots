# Releasing

Releases are driven by [commitizen](https://commitizen-tools.github.io/commitizen/),
the Python analogue of Node's `commit-and-tag-version`: it reads Conventional
Commits since the last tag, infers the next SemVer bump, rewrites
`CHANGELOG.md`, refreshes `uv.lock`, commits, and tags — then you push.

## Prerequisites

- `commitizen` is in the `dev` dependency group (`uv sync` installs it).
- A git remote named `origin` exists (create the repo with `gh repo create`,
  then `git remote add origin <url>`).
- Commits follow Conventional Commits (`feat:`, `fix:`, `chore:`, `doc:`, …).
  Run `uv run cz check` to confirm they parse before a release.

## Configuration

`pyproject.toml` -> `[tool.commitizen]`:

- `version_provider = "pep621"` — bumps `[project] version` (the single source
  of truth; `arabic_possible_roots.__version__` reads it back via
  `importlib.metadata`).
- `tag_format = "v$version"`, `annotated_tag = true` — matches the existing
  `v0.1.0` / `v0.5.0` annotated tags.
- `update_changelog_on_bump = true`, `changelog_file = "CHANGELOG.md"`.
- `pre_bump_hooks = ["uv lock"]` — refreshes `uv.lock`'s recorded version
  *after* the version files are bumped and *before* the commit, so the lockfile
  stays in the same release commit.

## Workflow

```bash
# 1. verify the suite is green
uv run pytest

# 2. bump, changelog, commit, and tag (infers major/minor/patch from commits)
uv run cz bump

# 3. push the commit and its tag
git push origin --follow-tags
```

Check that a given message (or range) parses, e.g.:

```bash
uv run cz check -m "feat: add something"      # one message
uv run cz check --rev-range v0.5.0..HEAD      # a git range
```

> One legacy commit (`b0bd011`, `doc: request considering reusability when
> coding`) uses `doc:` instead of `docs:` and so does **not** parse; `cz bump`
> ignores non-conforming messages when inferring the version, but strict
> `cz check --rev-range` will flag it. Either amend that message to `docs:` or
> force the bump with `uv run cz bump --increment minor`.

To override the inferred version:

```bash
uv run cz bump 1.0.0     # exact version
uv run cz bump minor     # force a minor bump
uv run cz bump --dry-run # preview without writing anything
```

The first `cz bump` will backfill `CHANGELOG.md` from the Conventional Commits
already on `main` since `v0.5.0`; later bumps append only the new section.

## What commitizen does *not* do

- It does **not** push (run `git push --follow-tags` yourself).
- It does **not** create GitHub Releases or publish to PyPI — only the local
  version bump, `CHANGELOG.md`, commit, and tag. Add a GitHub Action or
  `python-semantic-release` later if you want those.
