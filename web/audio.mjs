// Exact text and role matching prevents playing the wrong order or sample line.
export const voiceRole=speaker=>({OWNER:'owner',XIAOCHEN:'chen',GU:'gu',RIVAL:'rival',aunt:'aunt',narrator:'narrator'}[speaker]||'narrator');
export class VoicePlayer {
 constructor(clips=[],makeAudio=src=>new Audio(src),report=()=>{}) {this.clips=new Map(clips.map(c=>[c.role+'\n'+c.text,c.audio]));this.makeAudio=makeAudio;this.report=report;this.current=null;this.token=0;this.rate=1;}
 setRate(rate){this.rate=rate===0.8?0.8:1;if(this.current){this.current.playbackRate=this.rate;this.current.preservesPitch=true;}}
 find(role,text){return this.clips.get(role+'\n'+text);}
 stop(){this.token++;if(this.current){this.current.pause();this.current.currentTime=0;this.current=null;}this.report('');}
 async play(role,text){this.stop();const src=this.find(role,text);if(!src){this.report('Audio is not available for this line yet.');return false;}const token=this.token;const audio=this.makeAudio(src);this.current=audio;audio.playbackRate=this.rate;audio.preservesPitch=true;audio.onended=()=>{if(token===this.token){this.current=null;this.report('');}};audio.onerror=()=>{if(token===this.token){this.current=null;this.report('Could not play audio. Please try again.');}};this.report('Playing…');try{await audio.play();return token===this.token;}catch{if(token===this.token){this.current=null;this.report('Tap Listen to play this line.');}return false;}}
}
