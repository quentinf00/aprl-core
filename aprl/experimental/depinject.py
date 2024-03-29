import logging
from typing import Any, Callable

import toolz
from hydra_zen import instantiate, just
from omegaconf import OmegaConf

log = logging.getLogger(__name__)


def call(f):
    return f()


def to_list(d):
    l = [d[k] for k in sorted(d)]
    log.debug(f"Converted {d} to {l}")
    return l


KWARGS_PREFIX = "kwargs"
ARGS_PREFIX = "args"
STORE_PREFIX = "store"

PREFIXES = [STORE_PREFIX, KWARGS_PREFIX, ARGS_PREFIX]


def depinject(
    fn: Callable,
    flat_factories: dict[str, Callable],
    convert_to_list: None | list[str] = None,
    params: None | dict[str, Any] = None,
    paths: None | dict[str, str] = None,
):
    """
    Args:
        fn: callable to be injected with dependencies
        flat_factories: dictionary of callables that return the dependencies
        convert_to_list: list of path in the nested factory dict to convert to list
        params: placehoder argument for putting highlevel parameters for extension
        paths: placeholder argument for putting paths values
    """
    wrong_keys = [
        k for k in flat_factories if not any(k.startswith(p) for p in PREFIXES)
    ]
    if wrong_keys:
        log.warn(
            f"all factories keys should start with one of {PREFIXES}, {wrong_keys} will be ignored"
        )

    # From flat dot notation to nested dict of factories
    log.debug("Creating nested config of factories")
    factoried = dict()
    for k in sorted(flat_factories.keys(), reverse=False):
        kl = k.split(".")
        log.debug(f"Inserting {k} as {kl}")
        node_cfg = OmegaConf.create(just(flat_factories[k])())
        node_dict = OmegaConf.to_container(node_cfg)
        factoried = toolz.assoc_in(factoried, kl, node_dict)
    log.debug(f"Done : nested factory configs {factoried}")

    convert_to_list = convert_to_list or []
    log.debug(f"Will convert {convert_to_list} to list")
    updates_keys = sorted(list(flat_factories.keys()) + convert_to_list, reverse=True)
    for k in updates_keys:
        kl = k.split(".")
        if k in convert_to_list:
            log.debug(f"Converting {k} to list")
            factoried = toolz.update_in(factoried, kl, to_list)
        else:
            log.debug(f"Instantiating and calling {k}")
            factoried = toolz.update_in(
                factoried, kl, toolz.compose_left(instantiate, call)
            )

    # convert dict node to value list  + call each factory
    kwargs = factoried.get(KWARGS_PREFIX, dict())
    args = to_list(factoried.get(ARGS_PREFIX, {}))
    store = factoried.get(STORE_PREFIX, lambda x: x)
    store(fn(*args, **kwargs))
