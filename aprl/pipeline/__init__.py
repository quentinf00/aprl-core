import logging

import hydra
import hydra_zen

log = logging.getLogger(__name__)

store = hydra_zen.ZenStore(overwrite_ok=True)
stages_store = store(group="aprl/pipeline/stages", package="stages")
params_store = store(group="aprl/pipeline/params", package="params")


def run(to_run=[], stages=dict(), params=dict(), dry=False):
    log.info("Starting")
    for stage in to_run:
        log.info(f"Running stage {stage}")

        if hasattr(stages[stage], "func"):
            log.debug(stages[stage].func.__name__)
            log.debug(stages[stage].func.__doc__)
        elif hasattr(stages[stage], "__doc__"):
            log.debug(stages[stage].__doc__)

        if not dry:
            stages[stage]()
            log.info(f"Stage {stage} done")

    log.info("Done")


# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)


# Store the config
def register_pipeline(name, stages, params, help_msg="", default_sweep=None):
    if isinstance(params, dict):
        params = hydra_zen.make_config(**params)
    for stage_name, cfg in stages.items():
        stages_store(cfg, name=f"{name}-{stage_name}", package=f"stages.{stage_name}")
    params_store(params, name=name)
    store = hydra_zen.store()

    base_config = hydra_zen.builds(
        run,
        populate_full_signature=True,
        zen_partial=True,
    )

    help_msg = (
        "==============\n"
        + help_msg
        + """
Stages
\t"""
        + "\n\t".join([f"{s} -> {stages[s]._target_}" for s in sorted(stages)])
        + f"""
run  with "dry=True hydra.verbose=qf_pipeline" for detail help on each stage
use `to_run=[<stage_name>,...]` to run specify stages\n\n"""
    )

    _recipe = hydra_zen.make_config(
        to_run=tuple(sorted(stages)),
        bases=(base_config,),
        hydra=dict(
            sweeper=dict(params=default_sweep),
            help=dict(header=help_msg, app_name=name),
        ),
        hydra_defaults=[
            {"stages": [f"{name}-{stage_name}" for stage_name in stages]},
            {"params": name},
            "_self_",
        ],
    )
    store(
        _recipe,
        name=name,
        package="_global_",
        group="aprl/pipeline",
    )
    # Create a  partial configuration associated with the above function (for easy extensibility)

    store.add_to_hydra_store(overwrite_ok=True)
    stages_store.add_to_hydra_store(overwrite_ok=True)
    params_store.add_to_hydra_store(overwrite_ok=True)

    with hydra.initialize(version_base="1.3", config_path="."):
        cfg = hydra.compose(
            "aprl/pipeline/" + name,
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
        config_name="aprl/pipeline/" + name, version_base="1.3", config_path="."
    )(zen_endpoint)

    return api_endpoint, recipe, params
