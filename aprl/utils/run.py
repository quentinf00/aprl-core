import hydra_zen

import aprl.part
import aprl.utils

store = hydra_zen.ZenStore(overwrite_ok=True)
store(dict(), name="__placeholder", group="fn")


def add_fn(name: str, cfg):
    store(cfg, name=name, group="aprl/part/fn", package="fn")
    store.add_to_hydra_store(overwrite_ok=True)


aprl_run, aprl_cfg = aprl.part.register(aprl.utils.call)
aprl_pcfg = aprl.utils.make_partial(aprl_cfg)

if __name__ == "__main__":
    aprl_run()
