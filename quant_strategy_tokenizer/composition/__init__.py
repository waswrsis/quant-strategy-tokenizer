"""P2 composition and recipe generator API."""

from .contract import (
    RecipeContractCase,
    RecipeContractResult,
    RecipeContractSuite,
    contracts_pass,
    execute_recipe_instance,
    load_contract_suite,
    run_contract_suite,
)
from .fuzzing import FuzzingReport, check_fuzzing_meets_threshold, run_indicator_ewm_fuzzing
from .generator import (
    GeneratorConstraintError,
    RecipeGeneratorDocument,
    expand_builtin_recipe,
    expand_generator,
    load_generator_file,
    recipe_to_stable_json,
)
from .metamorphic import MetamorphicResult, metamorphic_pass, run_metamorphic_properties
from .verifier import check_temporal_safety_compatibility, upgrade_verification

__all__ = [
    "FuzzingReport",
    "GeneratorConstraintError",
    "MetamorphicResult",
    "RecipeContractCase",
    "RecipeContractResult",
    "RecipeContractSuite",
    "RecipeGeneratorDocument",
    "check_fuzzing_meets_threshold",
    "check_temporal_safety_compatibility",
    "contracts_pass",
    "execute_recipe_instance",
    "expand_builtin_recipe",
    "expand_generator",
    "load_contract_suite",
    "load_generator_file",
    "metamorphic_pass",
    "recipe_to_stable_json",
    "run_contract_suite",
    "run_indicator_ewm_fuzzing",
    "run_metamorphic_properties",
    "upgrade_verification",
]
