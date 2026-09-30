"""Infers anatomical joint names for a bipedal stick-figure mesh from pure
topology and geometry - independent of any specific analysis's body config
(see body_data.py, which is a separate, per-analysis concern: mass
distribution, supports, etc., keyed by the names this module produces).

Expected body plan (generic to this bipedal stick-figure convention, not
specific to any one .blend file):
  - "neck_base": the unique degree-4 joint - connects both shoulders, the
    head chain, and the spine/pelvis chain.
  - "spine_base": the unique degree-3 joint, one hop from neck_base -
    connects neck_base and both hip chains.
  - A head chain, 2 hops from neck_base: head_base, head_top (leaf).
  - Two arm chains, 4 hops from neck_base: shoulder, elbow, wrist, finger (leaf).
  - Two leg chains, 4 hops from spine_base (5 from neck_base): hip, knee,
    heel, toe (leaf).
  - Left/right is resolved from mesh geometry (not a fixed world axis) - see
    BodyGraphResolver.resolve() for details.
"""

from biomechanics.mesh_reader import MeshData

HEAD_CHAIN_NAMES = ["head_base", "head_top"]
ARM_CHAIN_NAMES = ["shoulder", "elbow", "wrist", "finger"]
LEG_CHAIN_NAMES = ["hip", "knee", "heel", "toe"]


def _build_adjacency(edge_indices):
    graph = {}
    for i, j in edge_indices:
        graph.setdefault(i, set()).add(j)
        graph.setdefault(j, set()).add(i)
    return graph


def _walk_chain(graph, start, came_from):
    """Walks a non-branching chain (degree <= 2) from `start` until a leaf,
    returning the ordered list of nodes [start, ..., leaf]."""
    chain = [start]
    prev, current = came_from, start
    while len(graph[current]) > 1:
        next_node = next(n for n in graph[current] if n != prev)
        chain.append(next_node)
        prev, current = current, next_node
    return chain


def _find_unique(candidates, predicate, description):
    matches = [n for n in candidates if predicate(n)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {description}, found {len(matches)}: {matches}")
    return matches[0]


def _subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _normalize(vector):
    length = _dot(vector, vector) ** 0.5
    if length == 0:
        raise ValueError(f"Cannot normalize a zero-length vector: {vector}")
    return tuple(c / length for c in vector)


def _perpendicular_component(vector, unit_axis):
    """Removes the component of `vector` along `unit_axis`."""
    component = _dot(vector, unit_axis)
    return tuple(v - component * a for v, a in zip(vector, unit_axis))


class BodyGraphResolver:
    """Infers {vertex_index: joint_name} for a bipedal stick-figure mesh
    using only its topology (vertex/edge connectivity) and geometry (vertex
    coordinates) - no dependency on any specific analysis's config.
    """

    def resolve(self, mesh_data: MeshData) -> dict:
        graph = _build_adjacency(mesh_data.edge_indices)
        coords = mesh_data.node_coords

        center = _find_unique(graph, lambda n: len(graph[n]) == 4, "degree-4 center joint")
        spine_base = _find_unique(
            graph[center], lambda n: len(graph[n]) == 3, "degree-3 spine joint adjacent to center"
        )

        names = {center: "neck_base", spine_base: "spine_base"}

        head_chain, arm_chains = self._classify_center_branches(graph, center, spine_base)
        for node, base_name in zip(head_chain, HEAD_CHAIN_NAMES):
            names[node] = base_name

        leg_chains = self._classify_spine_branches(graph, spine_base, center)

        up = _normalize(_subtract(coords[head_chain[-1]], coords[spine_base]))
        ref_chain, other_chain = arm_chains
        lateral_ref = _normalize(
            _perpendicular_component(_subtract(coords[ref_chain[0]], coords[center]), up)
        )
        # The one place an external convention is needed: a mirror-symmetric
        # figure can't reveal its own chirality from geometry alone. Use
        # world +X as "right" for the reference limb; every other bilateral
        # pair is then classified relative to this same reference (not
        # independently), so left/right stays internally consistent even if
        # the whole figure is rotated in world space.
        ref_is_right = coords[ref_chain[0]][0] > coords[other_chain[0]][0]

        for chain in arm_chains:
            self._assign_side(
                names, chain, ARM_CHAIN_NAMES, coords, center, up, lateral_ref, ref_is_right
            )
        for chain in leg_chains:
            self._assign_side(
                names, chain, LEG_CHAIN_NAMES, coords, spine_base, up, lateral_ref, ref_is_right
            )

        if len(names) != len(graph):
            unclassified = set(graph) - set(names)
            raise ValueError(f"Could not classify all joints, unclassified: {unclassified}")

        return names

    @staticmethod
    def _classify_center_branches(graph, center, spine_base):
        head_chain = None
        arm_chains = []
        for neighbor in graph[center]:
            if neighbor == spine_base:
                continue
            chain = _walk_chain(graph, neighbor, came_from=center)
            if len(chain) == len(HEAD_CHAIN_NAMES):
                head_chain = chain
            elif len(chain) == len(ARM_CHAIN_NAMES):
                arm_chains.append(chain)
            else:
                raise ValueError(f"Unexpected chain length {len(chain)} from center: {chain}")

        if head_chain is None:
            raise ValueError("Could not find head chain (length-2 branch from center)")
        if len(arm_chains) != 2:
            raise ValueError(f"Expected 2 arm chains from center, found {len(arm_chains)}")
        return head_chain, arm_chains

    @staticmethod
    def _classify_spine_branches(graph, spine_base, center):
        leg_chains = []
        for neighbor in graph[spine_base]:
            if neighbor == center:
                continue
            chain = _walk_chain(graph, neighbor, came_from=spine_base)
            if len(chain) != len(LEG_CHAIN_NAMES):
                raise ValueError(f"Unexpected leg chain length {len(chain)}: {chain}")
            leg_chains.append(chain)

        if len(leg_chains) != 2:
            raise ValueError(f"Expected 2 leg chains from spine_base, found {len(leg_chains)}")
        return leg_chains

    @staticmethod
    def _assign_side(names, chain, base_names, coords, branch_point, up, lateral_ref, ref_is_right):
        offset = _subtract(coords[chain[0]], coords[branch_point])
        lateral = _perpendicular_component(offset, up)
        same_side_as_ref = _dot(lateral, lateral_ref) >= 0
        is_right = same_side_as_ref == ref_is_right
        prefix = "r_" if is_right else "l_"
        for node, base_name in zip(chain, base_names):
            names[node] = prefix + base_name
