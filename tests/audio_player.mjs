import assert from 'node:assert/strict';
import {VoicePlayer,voiceRole} from '../web/audio.mjs';
const made=[],messages=[];
const make=src=>{const a={src,currentTime:2,paused:false,pause(){this.paused=true;},play:async()=>{}};made.push(a);return a;};
const p=new VoicePlayer([{role:'owner',text:'一共28元。',audio:'28.mp3'},{role:'owner',text:'一共31元。',audio:'31.mp3'}],make,m=>messages.push(m));
assert.equal(p.find('owner','一共27元。'),undefined);
assert.equal(p.find('gu','一共28元。'),undefined);
await p.play('owner','一共28元。');await p.play('owner','一共31元。');assert.equal(made[0].paused,true);assert.equal(made[0].currentTime,0);assert.equal(p.current.src,'31.mp3');
made[0].onended();assert.equal(p.current.src,'31.mp3'); // stale events cannot stop the new speaker
p.stop();assert.equal(made[1].paused,true);assert.equal(p.current,null);
assert.equal(await p.play('owner','missing'),false);assert.match(messages.at(-1),/not available/);
const blocked=new VoicePlayer([{role:'owner',text:'你好',audio:'hello.mp3'}],()=>({pause(){},play:async()=>{throw Error('autoplay blocked');}}));assert.equal(await blocked.play('owner','你好'),false);
assert.equal(voiceRole('RIVAL'),'rival');assert.equal(voiceRole('aunt'),'aunt');
console.log('Audio matching, cancellation, stale events and playback rejection checks passed');
p.setRate(.8);await p.play('owner','一共28元。');assert.equal(p.current.playbackRate,.8);assert.equal(p.current.preservesPitch,true);p.setRate(1);assert.equal(p.current.playbackRate,1);p.stop();
