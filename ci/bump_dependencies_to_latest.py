#!/usr/bin/env python3
import subprocess

import tomli

with open("pyproject.toml", "rb") as f:
    pyproject = tomli.load(f)
poetry = pyproject.get("tool").get("poetry")

deps = poetry.get("dependencies").keys()
deps = list(filter(("python").__ne__, deps))
deps = list(map(lambda d: f"{d}@latest", deps))
dev_deps = poetry.get("dev-dependencies").keys()
dev_deps = list(map(lambda d: f"{d}@latest", dev_deps))

subprocess.run(["poetry", "add"] + deps, check=True)
subprocess.run(["poetry", "add", "-D"] + dev_deps, check=True)
