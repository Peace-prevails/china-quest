// The speaker and expression are explicit per node, independently of story branches.
export function presentation(node, shots, state={}) {
 const shot=shots[node.id];
 if(shot)return {...shot,asset:shot.asset_by_item?.[state.item_selected]||shot.asset};
 let asset='BG02_SHOP_MAIN';
 if(node.scene_id==='S0')asset='BG01_HUTONG';
 else if(node.id.includes('door'))asset='BG04_DOOR';
 else if(node.id.includes('menu')||node.id==='water_card')asset='BG03_COUNTER';
 return {asset,speaker:node.speaker,expression:'environment',focus:'50% 50%'};
}
