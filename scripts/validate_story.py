"""Validate data contracts, asset dependency DAG and reachable story states."""
from collections import deque
from common import ROOT, read, manifest
from story import Story


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reachable(start, graph):
    seen, todo = set(), [start]
    while todo:
        current = todo.pop()
        if current not in seen:
            seen.add(current)
            todo.extend(graph[current])
    return seen


def validate_assets(data):
    assets = data['assets']
    ids = {a['id'] for a in assets}
    require(len(assets) == len(ids) == data['base_asset_count'] == 12, 'Expected 12 unique base assets')
    graph = {}
    for a in assets:
        require(a['category'] in {'backgrounds', 'characters', 'props', 'cg'}, 'Invalid asset category')
        require(a['prompt'] and a['candidate_target'] >= 1, 'Asset prompt/candidate count missing')
        require(set(a['reference_assets']) <= ids, 'Unknown reference asset')
        graph[a['id']] = a['reference_assets']
    def visit(aid, stack):
        require(aid not in stack, f'Asset dependency cycle: {aid}')
        for ref in graph[aid]:
            visit(ref, stack | {aid})
    for aid in ids:
        visit(aid, set())
    return ids


def validate_state_paths(data):
    """Traverse every reachable (node, story-state) pair, ignoring learning counters.

    Hotspot visits are observations, not branch conditions, so retain only states
    referenced by conditions or assignments. This bounds deliberate replay loops.
    """
    import copy
    import json
    story = Story()
    story.data = data
    story.nodes = {n['id']: n for n in data['nodes']}
    story.current = data['start']
    story.state = copy.deepcopy(data['initial_state'])
    # Visit history does not affect available transitions in EP01.
    def key(s):
        return (s.current, json.dumps({k: v for k, v in s.state.items() if k != 'explored_hotspots'}, sort_keys=True))
    queue = deque([story]); seen = {key(story)}; edges = {}; ends = set()
    while queue:
        current = queue.popleft(); source = key(current); edges[source] = []
        view = current.view()
        if view['kind'] == 'end':
            require(current.state['item_selected'] in {'beef', 'zhajiang'}, 'End without main dish')
            require(isinstance(current.state['spicy'], bool), 'End without spice decision')
            require(current.state['inheritance_response'] is not None, 'End without inheritance response')
            require(current.state['trust_alignment'] is not None, 'End without trust response')
            ends.add(source)
        for choice in view['choices']:
            if not all(current.state.get(k) == v for k, v in choice['requires'].items()):
                continue
            following = copy.copy(current)
            following.state = copy.deepcopy(current.state)
            following.learning = copy.deepcopy(current.learning)
            following.choose(choice['id'])
            target = key(following); edges[source].append(target)
            if target not in seen:
                seen.add(target); queue.append(following)
        require(len(seen) < 100000, 'State traversal exceeded safety limit')
    reverse = {s: [] for s in seen}
    for source, targets in edges.items():
        for target in targets:
            reverse[target].append(source)
    can_end = set(); todo = list(ends)
    while todo:
        state = todo.pop()
        if state not in can_end:
            can_end.add(state); todo.extend(reverse[state])
    require(can_end == seen, 'Reachable state has no path to ending')
    return len(seen), len(ends)


def validate():
    data = read(ROOT / 'episodes/ep01/episode_01.json')
    nodes = data['nodes']; ids = {n['id'] for n in nodes}
    require(len(ids) == len(nodes), 'Duplicate node IDs')
    assets = validate_assets(manifest())
    graph = {n['id']: [c['next'] for c in n['choices']] for n in nodes}
    require(data['start'] in ids, 'Unknown entry node')
    for n in nodes:
        require({'id', 'scene_id', 'speaker', 'zh', 'en', 'pinyin', 'asset_refs', 'learning_tags', 'choices'} <= n.keys(), f'Incomplete node {n.get("id")}')
        require(set(n['asset_refs']) <= assets, 'Unknown visual asset')
        require(bool(n['zh'] and n['en']), 'Missing translation')
        require(len({c['id'] for c in n['choices']}) == len(n['choices']), 'Duplicate choice IDs')
        for c in n['choices']:
            require({'id','zh','en','pinyin','next','set','requires'} <= c.keys(), 'Incomplete choice')
            require(c['next'] in ids, f'Unknown destination: {c["next"]}')
            require(set(c['set']) <= set(data['initial_state']), 'Unknown state assignment')
            require(set(c['requires']) <= set(data['initial_state']), 'Unknown precondition')
        require(bool(n['choices']) or n['kind'] == 'end', 'Dead end')
    require(reachable(data['start'], graph) == ids, 'Unreachable nodes')
    reverse = {x: [] for x in ids}
    for source, targets in graph.items():
        for target in targets:
            reverse[target].append(source)
    require(reachable('end', reverse) == ids, 'Node cannot reach end')
    require({s['id'] for s in data['scenes']} == {f'S{i}' for i in range(10)}, 'Expected S0–S9')
    states, endings = validate_state_paths(data)
    print(f'PASS: {len(nodes)} nodes; 10 scenes; 12 assets; {states} reachable states, {endings} ending states; no dead ends.')
    return {'nodes': len(nodes), 'scenes': 10, 'assets': len(assets), 'reachable_states': states, 'ending_states': endings}


if __name__ == '__main__':
    validate()
