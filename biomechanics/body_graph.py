"""Infers anatomical joint names, member (segment) names, and canonical
member direction for a bipedal stick-figure mesh from pure topology and
geometry, independent of any specific analysis's body config.

Expected body plan (generic to this bipedal stick-figure convention, not
specific to any one .blend file):
  - "neck_base" and "spine_base": the two branch joints (degree >= 3),
    directly connected to each other. Distinguished by their branch
    pattern, not by degree alone (spine_base is degree-3 normally, but
    degree-4 when a tail is present - see below) - neck_base is whichever
    one's other branches form 1 head chain + 2 arm chains.
  - A head chain, 2 hops from neck_base: head_base, head_top (leaf).
  - Two arm chains, 4 hops from neck_base: shoulder, elbow, wrist, finger (leaf).
  - Two leg chains, 4 hops from spine_base/5 from neck_base: hip, knee,
    heel, toe (leaf).
  - An optional tail off spine_base, present on some meshes - always
    exactly one joint, named "tail".
  - Left/right is resolved from mesh geometry (not a fixed world axis) - see
    BodyGraphResolver.resolve() for details.

Member direction convention (used for Pynite's i_node/j_node, and for what
cm_percent in body_data.py is measured from):
  - Limb members (arms, legs): i_node = proximal (nearer the trunk),
    j_node = distal (farther away) - cm_percent is "percent of the way from
    the proximal end".
  - Centerline members (spine, neck, head, tail): i_node = the physically
    higher joint, j_node = the lower one - cm_percent is "percent of the
    way down from the top". - TODO confirm this!
This is derived automatically here, not stored in body_data.py.
"""

from dataclasses import dataclass

from biomechanics.mesh_reader import MeshData

HEAD_CHAIN_NAMES = ["head_base", "head_top"]
ARM_CHAIN_NAMES = ["shoulder", "elbow", "wrist", "finger"]
LEG_CHAIN_NAMES = ["hip", "knee", "heel", "toe"]

# Member (segment) names, one per edge along [branch_point] + chain - i.e.
# ARM_MEMBER_NAMES[0] is the branch_point-to-shoulder segment, [1] is
# shoulder-to-elbow, etc. Same generic-bipedal-anatomy knowledge as the
# joint name lists above, just one level down (segments, not joints) -
# body_data.py only needs to provide mass/cm data per name, not identify
# which joints a member connects.
HEAD_MEMBER_NAMES = ["neck", "head"]
ARM_MEMBER_NAMES = ["back", "upperarm", "forearm", "hand"]
LEG_MEMBER_NAMES = ["pelvis", "thigh", "calf", "foot"]
SPINE_MEMBER_NAME = "spine"
TAIL_MEMBER_NAME = "tailbone"


@dataclass(frozen=True)
class BodyGraph:
    """Result of resolving a mesh: joint names, member names, and canonical
    member direction (all keyed by mesh vertex index, not by name).
    """

    names_by_index: dict  # dict[int, str]
    member_names_by_edge: dict  # dict[frozenset[int, int], str]
    direction_by_edge: dict  # dict[frozenset[int, int], tuple[int, int]] - (i_index, j_index)


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
    coordinates). 
    """

    def resolve(self, mesh_data: MeshData) -> BodyGraph:
        """Resolves joint names and canonical member direction for `mesh_data`."""
        graph = _build_adjacency(mesh_data.edge_indices)
        coords = mesh_data.node_coords

        center, spine_base, head_chain, arm_chains = self._find_center_and_spine(graph)

        names = {center: "neck_base", spine_base: "spine_base"}
        for node, base_name in zip(head_chain, HEAD_CHAIN_NAMES):
            names[node] = base_name

        leg_chains, tail_chain = self._classify_spine_branches(graph, spine_base, center)
        if tail_chain is not None:
            self._assign_tail(names, tail_chain)

        # Direction from spine base position to head top position
        up = _normalize(_subtract(coords[head_chain[-1]], coords[spine_base]))

        # Determine R/L reference vectors to assign R/L arms/legs
        # pylint false positive: _classify_center_branches raises unless
        # len(arm_chains) == 2, so this unpacking always has exactly 2 values.
        ref_chain, other_chain = arm_chains  # pylint: disable=unbalanced-tuple-unpacking
        lateral_ref = _normalize(
            _perpendicular_component(_subtract(coords[ref_chain[0]], coords[center]), up)
        )
        ref_is_right = coords[ref_chain[0]][0] > coords[other_chain[0]][0]

        member_names = {}
        direction = {}

        for chain in arm_chains:
            prefix = self._side_prefix(coords, center, chain, up, lateral_ref, ref_is_right)
            for node, base_name in zip(chain, ARM_CHAIN_NAMES):
                names[node] = prefix + base_name
            self._assign_limb_members(member_names, center, chain, ARM_MEMBER_NAMES, prefix)
            self._add_limb_direction(direction, center, chain)

        for chain in leg_chains:
            prefix = self._side_prefix(coords, spine_base, chain, up, lateral_ref, ref_is_right)
            for node, base_name in zip(chain, LEG_CHAIN_NAMES):
                names[node] = prefix + base_name
            self._assign_limb_members(member_names, spine_base, chain, LEG_MEMBER_NAMES, prefix)
            self._add_limb_direction(direction, spine_base, chain)

        if len(names) != len(graph):
            unclassified = set(graph) - set(names)
            raise ValueError(f"Could not classify all joints, unclassified: {unclassified}")

        self._assign_centerline_members(member_names, center, spine_base, head_chain, tail_chain)
        centerline_edges = self._centerline_edges(center, spine_base, head_chain, tail_chain)
        self._add_centerline_direction(direction, coords, up, centerline_edges)

        return BodyGraph(
            names_by_index=names, member_names_by_edge=member_names, direction_by_edge=direction
        )

    @staticmethod
    def _find_center_and_spine(graph):
        """Finds neck_base and spine_base among the mesh's branch joints
        (degree >= 3). 
        
        No tailbone: neck_base is degree-4 and spine_base is
        degree-3. 
        
        With tailbone: spine_base is degree-4 so we need to also
        distinguish by branch pattern (1 head chain + 2 arm chains).
        """
        branch_points = [n for n in graph if len(graph[n]) >= 3]

        # Validate 2 branch points
        if len(branch_points) != 2:
            raise ValueError(
                f"Expected exactly 2 branch joints (neck_base, spine_base), "
                f"found {len(branch_points)}: {branch_points}"
            )

        p, q = branch_points
        if q not in graph[p]:
            raise ValueError(
                f"Expected neck_base and spine_base to be directly connected, "
                f"but {p} and {q} are not"
            )

        # Try both assignments of neck_base and spine_base
        for center, spine_base in ((p, q), (q, p)):
            try:
                head_chain, arm_chains = BodyGraphResolver._classify_center_branches(
                    graph, center, spine_base
                )
                return center, spine_base, head_chain, arm_chains
            except ValueError:
                continue

        raise ValueError(
            f"Neither branch joint {p} nor {q} matches the expected neck_base "
            "pattern (1 head chain + 2 arm chains)"
        )

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
        """Returns (leg_chains, tail_chain). leg_chains is always the 2
        length-4 chains off spine_base. tail_chain is a single joint (a
        length-1 chain) if present, else None.
        """
        leg_chains = []
        other_chains = []
        for neighbor in graph[spine_base]:
            if neighbor == center:
                continue
            chain = _walk_chain(graph, neighbor, came_from=spine_base)
            if len(chain) == len(LEG_CHAIN_NAMES):
                leg_chains.append(chain)
            else:
                other_chains.append(chain)

        if len(leg_chains) != 2:
            raise ValueError(f"Expected 2 leg chains from spine_base, found {len(leg_chains)}")
        if len(other_chains) > 1:
            raise ValueError(
                f"Expected at most 1 extra (tail) chain from spine_base, "
                f"found {len(other_chains)}"
            )
        tail_chain = other_chains[0] if other_chains else None
        if tail_chain is not None and len(tail_chain) != 1:
            raise ValueError(
                f"Expected tail to be a single joint, found a chain of "
                f"length {len(tail_chain)}: {tail_chain}"
            )
        return leg_chains, tail_chain

    @staticmethod
    def _assign_tail(names, tail_chain):
        names[tail_chain[0]] = "tail"

    @staticmethod
    def _side_prefix(coords, branch_point, chain, up, lateral_ref, ref_is_right):
        offset = _subtract(coords[chain[0]], coords[branch_point])
        lateral = _perpendicular_component(offset, up)
        same_side_as_ref = _dot(lateral, lateral_ref) >= 0
        is_right = same_side_as_ref == ref_is_right
        return "r_" if is_right else "l_"

    @staticmethod
    def _assign_limb_members(member_names, branch_point, chain, base_names, prefix):
        """Names the edges along [branch_point] + chain, one per consecutive
        pair, using base_names (e.g. ARM_MEMBER_NAMES) in order."""
        full = [branch_point] + chain
        for (u, v), base_name in zip(zip(full[:-1], full[1:]), base_names):
            member_names[frozenset((u, v))] = prefix + base_name

    @staticmethod
    def _assign_centerline_members(member_names, center, spine_base, head_chain, tail_chain):
        member_names[frozenset((spine_base, center))] = SPINE_MEMBER_NAME

        full_head = [center] + head_chain
        for (u, v), base_name in zip(zip(full_head[:-1], full_head[1:]), HEAD_MEMBER_NAMES):
            member_names[frozenset((u, v))] = base_name

        if tail_chain is not None:
            member_names[frozenset((spine_base, tail_chain[0]))] = TAIL_MEMBER_NAME

    @staticmethod
    def _add_limb_direction(direction, branch_point, chain):
        """Limb convention: i_node = proximal (nearer the branch point),
        j_node = distal (farther away) - the natural branch-point-outward
        walk order.
        """
        full = [branch_point] + chain
        for proximal, distal in zip(full[:-1], full[1:]):
            direction[frozenset((proximal, distal))] = (proximal, distal)

    @staticmethod
    def _centerline_edges(center, spine_base, head_chain, tail_chain):
        edges = [(spine_base, center), (center, head_chain[0])]
        edges += list(zip(head_chain[:-1], head_chain[1:]))
        if tail_chain is not None:
            edges.append((spine_base, tail_chain[0]))
        return edges

    @staticmethod
    def _add_centerline_direction(direction, coords, up, edges):
        """Centerline convention: i_node = the physically higher joint
        (projected onto `up`), j_node = the lower one - independent of
        branch-point walk order, since that doesn't track height
        consistently across the whole centerline (e.g. spine_base is
        "outward" from neck_base along the spine, but downward, not up).
        """
        for u, v in edges:
            height_u = _dot(coords[u], up)
            height_v = _dot(coords[v], up)
            top, bottom = (u, v) if height_u >= height_v else (v, u)
            direction[frozenset((u, v))] = (top, bottom)
