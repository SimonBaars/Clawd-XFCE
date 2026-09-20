.PHONY: venv install test run prepare

venv:
	uv venv --system-site-packages --python /usr/bin/python3

install: venv
	uv pip install -e ".[dev]"
	.venv/bin/python -c "from clippy_xfce.sprites import ensure_assets; ensure_assets()"
	.venv/bin/python -c "from clippy_xfce.desktop import install_desktop_files; install_desktop_files(False)"
	mkdir -p $(HOME)/.local/bin
	ln -sfn $(PWD)/.venv/bin/clippy $(HOME)/.local/bin/clippy

prepare:
	.venv/bin/python -c "from clippy_xfce.sprites import ensure_assets; print(ensure_assets()[0].animations.keys())"

test:
	.venv/bin/python -m pytest

run:
	.venv/bin/clippy
