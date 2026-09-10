"""Runs Pynite's linear static analysis and extracts results."""

import logging

from Pynite import FEModel3D  # pylint: disable=wrong-import-position

from biomechanics.results import (
    DISPLACEMENT_THRESHOLD,
    REACTION_THRESHOLD,
    AnalysisResults,
    NodeDisplacement,
    NodeReaction,
    SupportWeight,
)


class AnalysisRunner:
    """Runs a linear static analysis on a constructed FEModel3D."""

    def __init__(
        self,
        model: FEModel3D,
        g: float,
        combo_name: str = "Combo",
        logger: logging.Logger | None = None,
    ):
        self._model = model
        self._g = g
        self._combo_name = combo_name
        self._logger = logger or logging.getLogger(__name__)

    def run(self) -> AnalysisResults:
        self._logger.info("\nPerforming linear analysis")
        self._model.analyze_linear(log=True, check_stability=True)

        displacements = []
        reactions = []
        weights_on_supports = []

        for name, node in self._model.nodes.items():
            dx = node.DX[self._combo_name]
            dy = node.DY[self._combo_name]
            dz = node.DZ[self._combo_name]
            if any(abs(v) > DISPLACEMENT_THRESHOLD for v in (dx, dy, dz)):
                displacements.append(NodeDisplacement(name, dx, dy, dz))

            rx = node.RxnFX[self._combo_name]
            ry = node.RxnFY[self._combo_name]
            rz = node.RxnFZ[self._combo_name]
            if any(abs(v) > REACTION_THRESHOLD for v in (rx, ry, rz)):
                reactions.append(NodeReaction(name, rx, ry, rz))

                # Calculate downwards weight (kg) on supported nodes
                # Flip sign because reaction force is in +Z direction
                weights_on_supports.append(SupportWeight(name, -int(rz / self._g)))

        return AnalysisResults(
            displacements=displacements,
            reactions=reactions,
            weights_on_supports=weights_on_supports,
        )
