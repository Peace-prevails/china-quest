import fs from 'node:fs';
import assert from 'node:assert/strict';
import {presentation} from '../web/visuals.mjs';
const data=JSON.parse(fs.readFileSync('episodes/ep01/episode_01.json'));
const shots=JSON.parse(fs.readFileSync('web/scene_visuals.json'));
const byId=Object.fromEntries(data.nodes.map(n=>[n.id,n]));
for(const n of data.nodes){const v=presentation(n,shots);if(n.speaker!=='narrator'){assert.equal(v.speaker,n.speaker,n.id);assert.ok(v.asset.startsWith('DLG_')||v.asset==='CG01_FILE_SLAM'||v.asset.startsWith('BEAT_'),n.id);assert.notEqual(v.expression,'environment');}}
for(const id of Object.keys(shots))assert.ok(byId[id],id);
assert.equal(presentation(byId.gu_eat,shots).speaker,'OWNER');
assert.equal(presentation(byId.reply_chen0,shots).asset,'DLG_CHEN_FRIENDLY');
assert.equal(presentation(byId.reply_chen2,shots).asset,'DLG_CHEN_UNSURE');
assert.equal(presentation(byId.name,shots).asset,'DLG_OWNER_GUARDED');
assert.equal(presentation(byId.inherit_reject,shots).asset,'DLG_GU_HESITANT');
assert.equal(presentation(byId.hotspot_door,shots).asset,'BG04_DOOR');
console.log('PASS every spoken node has a matching character shot; expression switches and narrator backgrounds match.');

assert.equal(presentation(byId.served,shots,{item_selected:"zhajiang"}).asset,"BEAT_MEAL_ZHAJIANG");
assert.equal(presentation(byId.served,shots,{item_selected:"beef"}).asset,"BEAT_MEAL_BEEF");
