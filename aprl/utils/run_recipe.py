import logging
from typing import Any, Callable


def run_recipe(
    inp: None | Any = None,
    steps: None | dict[str, Callable] = None,
    params: None | dict = None,
):
    log = logging.getLogger("run_recipe")
    log.info("Starting simple chaining with steps:")
    log.info("\n".join(sorted(steps)))
    log.debug(f"{params=}")

    if not steps:
        log.info("No steps returning input")
        return inp

    sorted_steps = sorted(steps)
    if inp is None:
        log.info("No input given, computing it from first step")
        k = sorted_steps.pop(0)
        log.info(("Running ", k, steps[k]))
        inp = steps[k]()
        log.debug((k, "Input ", inp))

    for k in sorted_steps:
        log.info(("Running ", k, steps[k]))
        log.debug((k, "Input ", inp))
        inp = steps[k](inp)
        log.debug((k, "Output ", inp))
