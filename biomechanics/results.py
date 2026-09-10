"""Post-analysis results: displacements, reactions, and support weights."""

import logging
from dataclasses import dataclass

from Pynite import FEModel3D  # pylint: disable=wrong-import-position

DISPLACEMENT_THRESHOLD = 1e-3
REACTION_THRESHOLD = 1e-3


@dataclass(frozen=True)
class NodeDisplacement:
    name: str
    dx: float
    dy: float
    dz: float


@dataclass(frozen=True)
class NodeReaction:
    name: str
    rx: float
    ry: float
    rz: float


@dataclass(frozen=True)
class SupportWeight:
    name: str
    weight_kg: float


@dataclass(frozen=True)
class AnalysisResults:
    displacements: list[NodeDisplacement]
    reactions: list[NodeReaction]
    weights_on_supports: list[SupportWeight]

    def log_summary(self, logger: logging.Logger) -> None:
        logger.info("Nodal displacements (meters):")
        for d in self.displacements:
            logger.info("%s: DX=%.2f  DY=%.2f  DZ=%.2f", d.name, d.dx, d.dy, d.dz)

        logger.info("\nReaction forces (Newtons):")
        for r in self.reactions:
            logger.info("%s: RxnFX=%.2f  RxnFY=%.2f  RxnFZ=%.2f", r.name, r.rx, r.ry, r.rz)

        logger.info("Weight exerted on support nodes (kg):")
        for w in self.weights_on_supports:
            logger.info("%s: %.2f", w.name, w.weight_kg)


def log_model_summary(model: FEModel3D, logger: logging.Logger) -> None:
    """Logs nodes, members, point loads, and supports of a constructed model."""
    logger.info("\nNodes: %d", len(model.nodes))
    for name, node in model.nodes.items():
        logger.info("%s: (%.2f, %.2f, %.2f)", name, node.X, node.Y, node.Z)

    logger.info("\nMembers: %d", len(model.members))
    for name, member in model.members.items():
        i = member.i_node.name
        j = member.j_node.name
        logger.info("%s: %s -> %s", name, i, j)

    logger.info("\nMember point loads:")
    for name, member in model.members.items():
        for load in member.PtLoads:
            direction, magnitude, x, case = load
            logger.info("%s: %s = %s", name, direction, magnitude)

    logger.info("\nSupports:")
    for name, node in model.nodes.items():
        if any(
            [
                node.support_DX,
                node.support_DY,
                node.support_DZ,
                node.support_RX,
                node.support_RY,
                node.support_RZ,
            ]
        ):
            logger.info(name)
