from common import ROOT,read,manifest

def validate():
 d=read(ROOT/'episodes/ep01/episode_01.json');nodes=d['nodes'];ids={n['id'] for n in nodes};assert len(ids)==len(nodes),'Duplicate IDs'
 assets={a['id'] for a in manifest()['assets']};graph={n['id']:[c['next'] for c in n['choices']] for n in nodes}
 assert len(assets)==12
 for n in nodes:
  assert {'id','scene_id','speaker','zh','en','pinyin','asset_refs','learning_tags','choices'}<=n.keys()
  assert set(n['asset_refs'])<=assets
  assert n['zh'] and n['en']
  for c in n['choices']:
   assert c['next'] in ids,(n['id'],c['next'])
   assert set(c['set'])<=set(d['initial_state'])
  assert n['choices'] or n['kind']=='end','Dead end'
 def walk(start,g):
  seen=set();todo=[start]
  while todo:
   x=todo.pop()
   if x not in seen:seen.add(x);todo.extend(g[x])
  return seen
 assert walk(d['start'],graph)==ids,'Unreachable nodes'
 reverse={x:[] for x in ids}
 for x,targets in graph.items():
  for y in targets:reverse[y].append(x)
 assert walk('end',reverse)==ids,'Node cannot reach end'
 # Exploration is deliberately replayable; all cycles have an exit to the main story.
 assert {s['id'] for s in d['scenes']}=={f'S{i}' for i in range(10)}
 print(f'PASS: {len(nodes)} nodes; 10 scenes; 12 assets; all nodes reachable and can reach end.')
if __name__=='__main__':validate()
