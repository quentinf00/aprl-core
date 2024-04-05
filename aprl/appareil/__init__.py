import logging
from typing import Callable

import hydra
import hydra_zen

log = logging.getLogger(__name__)

store = hydra_zen.ZenStore(overwrite_ok=True)
parts_store = store(group="aprl/appareil/part", package="part")
params_store = store(group="aprl/appareil/params", package="params")


def run(
    to_run: list[str] = [],
    parts: dict[str, Callable] = dict(),
    params: dict = dict(),
    dry: bool = False,
):
    """

    Args:
        to_run: list of parts to run
        parts: dictionary of stage function
        params: Place holder for exposing values that can be used in stage configurations
        dry: if true does not execute the parts (can be useful for dispalying logs and debugging)
    """
    log.info("Starting")
    for stage in to_run:
        log.info(f"Running stage {stage}")

        if hasattr(parts[stage], "func"):
            log.debug(parts[stage].func.__name__)
            log.debug(parts[stage].func.__doc__)

        elif hasattr(parts[stage], "__doc__"):
            log.debug(parts[stage].__doc__)

        if not dry:
            parts[stage]()
            log.info(f"Stage {stage} done")

    log.info("Done")


# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)


# Store the config
def register(
    name: str, parts: dict, params: dict, help_msg="", default_sweep: dict = None
):
    """
    Register a aprl appareil config and return appareil hydra entrypoint and
    the Config recipe to generate new configuration

    Args:
        help_msg (): Message describing the parameter values
        name: Name of the appareil used for declaring the Config
        parts: mapping of stage name to stage function to be called
        params: dictionnary of the appareil parameters, declared in separate config group for easy extension
        default_sweep: default multirun configuration

    Returns:  appareil hydra main and appareil config recipe

    """
    if isinstance(params, dict):
        params = hydra_zen.make_config(**params)

    for stage_name, cfg in parts.items():
        parts_store(cfg, name=f"{name}-{stage_name}", package=f"parts.{stage_name}")
    params_store(params, name=name)
    store = hydra_zen.store()

    base_config = hydra_zen.builds(
        run,
        populate_full_signature=True,
        zen_partial=True,
    )

    help_msg = (
        "=============="
        + ""
        + help_msg
        + ""
        + """
parts
\t"""
        + "\n\t".join([f"{s} -> {parts[s]._target_}" for s in sorted(parts)])
        + ""
        + f"""
run  with "dry=True hydra.verbose=aprl.appareil" for displaying the doc of each stage
use `to_run=[<stage_name>,...]` to run specify parts\n\n"""
        + ""
        + ""
    )

    _recipe = hydra_zen.make_config(
        to_run=tuple(sorted(parts)),
        bases=(base_config,),
        hydra=dict(
            sweeper=dict(params=default_sweep),
            help=dict(header=help_msg, app_name=name),
        ),
        hydra_defaults=[
            {"parts": [f"{name}-{stage_name}" for stage_name in parts]},
            {"params": name},
            "_self_",
        ],
    )
    store(
        _recipe,
        name=name,
        package="_global_",
        group="aprl/appareil",
    )
    # Create a  partial configuration associated with the above function (for easy extensibility)

    store.add_to_hydra_store(overwrite_ok=True)
    parts_store.add_to_hydra_store(overwrite_ok=True)
    params_store.add_to_hydra_store(overwrite_ok=True)

    with hydra.initialize(version_base="1.3", config_path="."):
        cfg = hydra.compose(
            "aprl/appareil/" + name,
        )

    recipe = hydra_zen.make_config(
        **{
            k: node
            for k, node in cfg.items()
            if k not in ("_target_", "_partial_", "_args_", "_convert_", "_recursive_")
        },
        bases=(base_config,),
        zen_dataclass={
            "cls_name": f'{"".join(x.capitalize() for x in name.lower().split("_"))}Recipe'
        },
    )
    # Create CLI endpoint
    api_endpoint = hydra.main(
        config_name="aprl/appareil/" + name, version_base="1.3", config_path="."
    )(zen_endpoint)

    return api_endpoint, recipe, params
