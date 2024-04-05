import dataclasses
import logging
from functools import partial
from pathlib import Path
from typing import Any, Callable

import hydra_zen
import toolz

log = logging.getLogger(__name__)

import hydra_zen
import toolz
from omegaconf import OmegaConf


def call(fn: Callable):
    return fn()


def aprlify(fn: Callable, inject: dict[str, Callable], params: dict[str, Any]):
    log.debug(f"Params {params}")
    log.debug(f"Injecting {inject} to {fn}")
    fn_cfg = OmegaConf.create(hydra_zen.builds(fn))
    fn_dict = OmegaConf.to_container(fn_cfg)

    for k in sorted(inject.keys(), reverse=False):
        kl = k.split(".")
        log.debug(f"Inserting {k} as {kl}")
        factory_cfg = OmegaConf.create(hydra_zen.just(inject[k]))
        factory_dict = OmegaConf.to_container(factory_cfg)
        fn_dict = toolz.assoc_in(fn_dict, kl, factory_dict)

    log.debug(f"Inserted {fn_dict}")
    log.debug(f"Instantiating...")
    for k in sorted(list(inject.keys()), reverse=True):
        kl = k.split(".")
        log.debug(f"Instantiating and calling {k}, {toolz.get_in(kl, fn_dict)}")
        fn_dict = toolz.update_in(
            fn_dict, kl, toolz.compose_left(hydra_zen.instantiate, call)
        )

    log.debug(f"Injected {fn_dict}")
    return hydra_zen.instantiate(fn_dict)()


def kw2a(fn, **kwargs):
    return fn(*[kwargs[k] for k in sorted(kwargs)])


compose = partial(kw2a, fn=partial(toolz.compose_left))


def make_partial(cfg: type):
    pcfg = dataclasses.make_dataclass(
        cls_name=f"Partial",
        fields=[("_partial_", bool, dataclasses.field(default=True))],
        kw_only=True,
    )
    return dataclasses.make_dataclass(
        cls_name=f"Partial{cfg.__name__}",
        fields=[],
        bases=(pcfg, cfg),
    )


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
