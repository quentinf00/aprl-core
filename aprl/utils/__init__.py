from pathlib import Path


def mkp(path, isdir=None):
    p = Path(path)
    if isdir is None:
        isdir = p.suffix == ""

    if isdir:
        p.mkdir(parents=True, exist_ok=True)
    else:
        p.parent.mkdir(parents=True, exist_ok=True)

    return p


def register_resolvers():
    from omegaconf import OmegaConf

    OmegaConf.register_new_resolver("aprl-mkp", mkp, replace=True)
