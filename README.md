# Appareil [\a.pa.ʁɛj\]

_Whole composed of pieces aimed at working together_

Examples of Appareils:
- Architectural: "Appareil de défense": Arrangement and layout of stones in a masonry structure
- Legal: "Appareil des loi": Set of laws destined to work together
- Biology: "Appareil digestif": System of organs that collaborate for digestive purposes
- Culinary: "Appareil à quiche": The mixed ingredients that form the base of quiche
- Tech: "Appareil électrique": Electrical device made of multiple parts


## Motivation:
Define a simple way to write software as to easily:
    - reuse existing parts for new usecases
    - composing parts for new purposes
    - adding more parts that can easily interact with the rest of the ecosystem

## Solution:
The idea is to heavily rely on hydra and hydra_zen to automatically register python functions of interest to the hydra store.
Then we get for free:
    - Extension of functionalities by defining new configurations
    - Configurable CLI 
    - Parallel and HPC jobs using launchers
Appareil adds:
    - Simple logic for defining chain of functions and exposing most useful config fields
    - hydra based dependency injection helper to convert _any_ python function to a **part**
    - Next: easy integration with dvc for simple data versioning and pipeline execution management


## Concepts:
In order 
### Part:
    Elementary building block. 
    
### Appareil:
    Orchestrated Parts

## Tools:
    - hydra
    - hydra-zen
