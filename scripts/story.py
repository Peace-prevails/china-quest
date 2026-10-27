from common import ROOT,read
class Story:
 def __init__(self):
  self.data=read(ROOT/'episodes/ep01/episode_01.json');self.nodes={n['id']:n for n in self.data['nodes']};self.state=self.data['initial_state'].copy();self.state['explored_hotspots']=[];self.learning={'hint_usage':{},'phrase_exposure':{},'replay_count':0};self.current=self.data['start']
 def values(self):
  item=next((x for x in self.data['menu'] if x['id']==self.state['item_selected']),None)
  return {'item_name':item['zh'] if item else '', 'item_en':item['en'] if item else '', 'item_price':item['price'] if item else 0,'total':(item['price'] if item else 0)+(3 if self.state['wants_water'] else 0)}
 def view(self):
  n=self.nodes[self.current];return {**n,'zh':n['zh'].format(**self.values()),'en':n['en'].format(**self.values())}
 def choose(self,choice_id):
  n=self.nodes[self.current];c=next(c for c in n['choices'] if c['id']==choice_id)
  if not all(self.state.get(k)==v for k,v in c['requires'].items()):raise ValueError('Choice precondition failed')
  if c['next'] in ['spice','confirm'] and not self.state['item_selected'] and not c['set'].get('item_selected'):raise ValueError('Select a main dish first')
  for tag in n['learning_tags']:self.learning['phrase_exposure'][tag]=self.learning['phrase_exposure'].get(tag,0)+1
  if '听不懂' in c['zh']:self.learning['hint_usage'][n['scene_id']]=self.learning['hint_usage'].get(n['scene_id'],0)+1
  self.state.update(c['set']);self.current=c['next']
  hotspot=self.nodes[self.current].get('on_enter',{}).get('append_explored_hotspots')
  if hotspot and hotspot not in self.state['explored_hotspots']:self.state['explored_hotspots'].append(hotspot)
  return self.view()
if __name__=='__main__':
 import json
 s=Story()
 while True:
  n=s.view();print('\n'+n['zh']+'\n'+n['en'])
  for line in n.get('conditional_lines',[]):
   if all(s.state.get(k)==v for k,v in line['requires'].items()):print(line['zh'],line['en'])
  if not n['choices']:break
  for i,c in enumerate(n['choices']):print(f'{i+1}. {c["zh"]} / {c["en"]}')
  try:s.choose(n['choices'][int(input('> '))-1]['id'])
  except (ValueError,IndexError):print('Choose a listed number.')
 from common import write
 write(ROOT/'local/episode_01_state.json',{'story':s.state,'learning':s.learning})
 print('Saved local/episode_01_state.json')
