"""Matrix engine: resource transfer matrix and spectral analysis."""

from .capped import CappedTransferSystem
from .family import MatrixFamily
from .irreducibility import (
    condensation_summary,
    is_irreducible,
    strongly_connected_components,
)
from .matrix_validator import validate_matrix
from .perron import perron_analysis, perron_vector
from .transfer_matrix import MatrixValidationError, TransferMatrix

__all__ = [
    "TransferMatrix",
    "MatrixValidationError",
    "CappedTransferSystem",
    "MatrixFamily",
    "perron_vector",
    "perron_analysis",
    "validate_matrix",
    "is_irreducible",
    "strongly_connected_components",
    "condensation_summary",
]
