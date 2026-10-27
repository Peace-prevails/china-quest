import copy
from common import ROOT,read,write
class Story:
 def __init__(self):
  self.data=read(ROOT/'episodes/ep01/episode_01.json');self.nodes={n['id']:n for n in self.data['nodes']};self.state=self.data['initial_state'].copy();self.state['explored_hotspots']=[];self.learning={'hint_usage':{},'phrase_exposure':{},'replay_count':0};self.current=self.data['start']
 def values(self):
  item=next((x for x in self.data['menu'] if x['id']==self.state['item_selected']),None)
  return {'item_name':item['zh'] if item else '', 'item_en':item['en'] if item else '', 'item_price':item['price'] if item else 0,'total':(item['price'] if item else 0)+(3 if self.state['wants_water'] else 0)}
 def view(self):
  n=self.nodes[self.current]
  return {**n,'zh':n['zh'].format(**self.values()),'en':n['en'].format(**self.values()),'conditional_lines':[line for line in n.get('conditional_lines',[]) if all(self.state.get(k)==v for k,v in line['requires'].items())]}
 def choose(self,choice_id):
  n=self.nodes[self.current]
  c=next((c for c in n['choices'] if c['id']==choice_id),None)
  if c is None:raise ValueError('Unknown choice')
  if not all(self.state.get(k)==v for k,v in c['requires'].items()):raise ValueError('Choice precondition failed')
  if c['next'] in ['spice','confirm'] and not self.state['item_selected'] and not c['set'].get('item_selected'):raise ValueError('Select a main dish first')
  for tag in n['learning_tags']:self.learning['phrase_exposure'][tag]=self.learning['phrase_exposure'].get(tag,0)+1
  if '听不懂' in c['zh']:self.learning['hint_usage'][n['scene_id']]=self.learning['hint_usage'].get(n['scene_id'],0)+1
  self.state.update(c['set']);self.current=c['next']
  hotspot=self.nodes[self.current].get('on_enter',{}).get('append_explored_hotspots')
  if hotspot and hotspot not in self.state['explored_hotspots']:self.state['explored_hotspots'].append(hotspot)
  return self.view()
 def save(self,path=None):
  write(path or ROOT/'local/episode_01_state.json',{'version':1,'episode_id':self.data['id'],'current':self.current,'story':self.state,'learning':self.learning})
 def load(self,path=None):
  saved=read(path or ROOT/'local/episode_01_state.json')
  if saved.get('version')!=1 or saved.get('episode_id')!=self.data['id']:raise ValueError('Unsupported episode save')
  if saved.get('current') not in self.nodes:raise ValueError('Unknown saved node')
  state=saved.get('story',{});learning=saved.get('learning',{})
  if set(state)!=set(self.data['initial_state']):raise ValueError('Invalid saved state fields')
  if state['item_selected'] not in [None,'beef','zhajiang']:raise ValueError('Invalid saved main dish')
  for field in ['wants_water','asked_directions','used_help_location','saw_red_envelope']:
   if type(state[field]) is not bool:raise ValueError('Invalid saved boolean: '+field)
  if state['spicy'] is not None and type(state['spicy']) is not bool:raise ValueError('Invalid saved spice')
  if not isinstance(state['explored_hotspots'],list) or not all(x in ['owner','chen','menu','envelope','door'] for x in state['explored_hotspots']):raise ValueError('Invalid hotspot history')
  if not isinstance(learning.get('hint_usage'),dict) or not isinstance(learning.get('phrase_exposure'),dict) or type(learning.get('replay_count')) is not int:raise ValueError('Invalid learning record')
  self.state=copy.deepcopy(state);self.learning=copy.deepcopy(learning);self.current=saved['current']
  return self.view()
 def replay_exploration(self):
  if self.current!='end':raise ValueError('Finish the episode before replaying exploration')
  # Replay is an isolated copy: completed EP02 handoff remains unchanged.
  replay=copy.copy(self);replay.state=copy.deepcopy(self.state);replay.learning=copy.deepcopy(self.learning)
  replay.current='explore';replay.learning['replay_count']+=1
  return replay

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');parser.add_argument('--replay-exploration',action='store_true');args=parser.parse_args()
 s=Story()
 if args.resume or args.replay_exploration:s.load()
 if args.replay_exploration:s=s.replay_exploration()
 save_path=ROOT/'local'/('episode_01_replay.json' if args.replay_exploration else 'episode_01_state.json')
 while True:
  n=s.view();print('\n'+n['zh']+'\n'+n['en'])
  for line in n['conditional_lines']:print(line['zh'],line['en'])
  if not n['choices']:break
  for i,c in enumerate(n['choices']):print(f'{i+1}. {c["zh"]} / {c["en"]}')
  try:
   raw=input('> (q saves and quits) ')
   if raw.strip().lower()=='q':break
   number=int(raw)
   if number<1 or number>len(n['choices']):raise ValueError('Invalid choice number')
   s.choose(n['choices'][number-1]['id']);s.save(save_path)
  except (ValueError,IndexError):print('Choose a listed number.')
  except (EOFError,KeyboardInterrupt):break
 s.save(save_path);print('Saved',save_path)
