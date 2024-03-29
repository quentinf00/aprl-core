import hydra
import hydra_zen

store = hydra_zen.ZenStore(overwrite_ok=True)
store(dict(defaults=[{"aprl/mod": "???"}]), name="base_qf_module")

mods_store = store(group="aprl/mod", package="_global_")

store(
    dict(), name="__placeholder", group="args"
)  # see https://github.com/facebookresearch/hydra/issues/2875
args_store = store(group="aprl/mod/args", package="_global_")


# Store the config
def register(fn, base_args=None, help_msg=None, default_sweep=None, name=None):
    if name is None:
        name = fn.__name__
    if help_msg is None:
        help_msg = f"""

         {fn.__name__=} function wrapped in hydra 
        """ + (fn.__doc__ or "")

    base_config = hydra_zen.builds(
        fn,
        populate_full_signature=True,
        zen_partial=False,
    )

    if base_args is None:
        base_args = dict()

    base_args = hydra_zen.make_config(
        **base_args,
        bases=(base_config,),
        zen_dataclass={
            "cls_name": f'{"".join(x.capitalize() for x in name.lower().split("_"))}OcbModArgs'
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
            "_self_",
        ],
    )

    mods_store(_recipe, name=name)
    store.add_to_hydra_store(overwrite_ok=True)

    # Create CLI endpoint
    api_endpoint = hydra.main(
        config_name="aprl/mod/" + name, version_base="1.3", config_path="."
    )(hydra_zen.zen(fn))

    return api_endpoint, base_args
