import fs from 'node:fs';
import assert from 'node:assert/strict';
import {Story} from '../web/engine.mjs';
const {data,cases}=JSON.parse(fs.readFileSync(0,'utf8'));
for(const fixture of cases){const s=new Story(data);for(const id of fixture.choices)s.choose(id);assert.deepEqual(s.save(),fixture.expected);const loaded=new Story(data);loaded.load(s.save());assert.deepEqual(loaded.view(),s.view());const replay=s.replay();replay.state.explored_hotspots.push('door');assert.notDeepEqual(replay.state,s.state);assert.equal(s.current,'end');assert.equal(replay.current,'explore');}
const s=new Story(data);assert.throws(()=>s.choose('missing'));const save=s.save();save.story.wants_water='false';assert.throws(()=>s.load(save));assert.throws(()=>s.replay());s.current='billion';assert.equal(s.view().conditional_lines.length,0);s.state.saw_red_envelope=true;assert.equal(s.view().conditional_lines.length,1);
console.log(`PASS ${cases.length} browser/Python story parity routes, save restore, replay isolation and invalid input`);
