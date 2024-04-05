from typing import Callable

import hydra
import hydra_zen

store = hydra_zen.ZenStore(overwrite_ok=True)
overrides_store = store(group="aprl/overrides", package="_global_")
store(dict(), name="__placeholder", group="overrides", package="_global_")
overrides_store(dict(), name="none")
store.add_to_hydra_store(overwrite_ok=True)

parts_store = store(group="aprl", package="_global_")

store(
    dict(), name="__placeholder", group="args"
)  # see https://github.com/facebookresearch/hydra/issues/2875
args_store = store(group="aprl/args", package="_global_")


# Store the config
def register(
    fn: Callable,
    base_args: dict | None = None,
    help_msg: str | None = None,
    default_sweep: dict | None = None,
    name: str | None = None,
    builds_kws: dict | None = None,
    zen_kws: dict | None = None,
) -> tuple[Callable, type]:
    """
    Generate hydra config corresponding to fn
    Register basic config with base_args values in group /aprl/part with name <name>
    Generate hydra endpoint for configurable CLI
    returns hydra endpoint and Dataclass to instantiate endpoint configurations

    Args:
        fn: Callable to be aprled
        base_args: Default configuration values, keys of the dictionnary should be arguments of fn
        help_msg: Help message to display when running CLI with --help. Default to fn.__doc__
        default_sweep: Configure default multirun configuration to launch with -m flag
        name: Config name in the store, default to fn.__name__
        builds_kws: Keyword arguments to be passed to hydra_zen.builds(fn, populate_full_signature=True, **kw),
        zen_kws: Keyword arguments to be passed to hydra_zen.builds(fn, **kw),

    Returns: hydra wrapped endpoint and Config dataclass

    """
    builds_kws = builds_kws or dict()
    zen_kws = zen_kws or dict()
    if name is None:
        name = fn.__name__
    if help_msg is None:
        help_msg = f"""

         {fn.__name__=} function wrapped in hydra 
        """ + (fn.__doc__ or "")

    base_config = hydra_zen.builds(
        fn,
        **(dict(populate_full_signature=True, zen_partial=False) | builds_kws),
    )

    if base_args is None:
        base_args = dict()

    base_args = hydra_zen.make_config(
        **base_args,
        bases=(base_config,),
        zen_dataclass={
            "cls_name": f'{"".join(x.capitalize() for x in name.lower().split("_"))}AprlPartArgs'
        },
    )

    args_store(base_args, name=name)

    _recipe = dict(
        hydra=dict(
            sweeper=dict(params=default_sweep),
            help=dict(header=help_msg, app_name=name),
        ),
        defaults=[
            {"args": name},
            {"overrides": "none"},
            "_self_",
        ],
    )

    parts_store(_recipe, name=name)
    store.add_to_hydra_store(overwrite_ok=True)
    overrides_store.add_to_hydra_store(overwrite_ok=True)

    # Create CLI endpoint
    api_endpoint = hydra.main(
        config_name="aprl/" + name, version_base="1.3", config_path="."
    )(hydra_zen.zen(fn, **zen_kws))

    return api_endpoint, base_args
