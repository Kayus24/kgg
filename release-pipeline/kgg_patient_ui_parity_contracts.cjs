"use strict";
// Independent oracle for the deliberately fixed synthetic fixture, not a second app implementation.
const EXPECTED={
 'pair-kg':{pair1:['','']},'pair-wdh':{pair1:['','']},
 'remaining-kg':{pair1:['','12']},'pair-complete':{pair1:['15','12']},
 'manual-zero':{pair2:['','']},'cancelled':{pair2:['','']},'saved-zero':{pair2:['0','']},
 'center-complete':{pair3:['25','9']},
 'lr-left':{left:['11','8'],right:['','']},'lr-right':{left:['11','8'],right:['13','9']},
 'seconds-complete':{timer:['','45']},
 'reloaded':{pair1:['15','12'],pair2:['0',''],pair3:['25','9'],left:['11','8'],right:['13','9'],timer:['','45']}
};
const CLOSED=new Set(['pair-complete','cancelled','saved-zero','center-complete','lr-left','lr-right','seconds-complete','reloaded']);
function validateFixtureState(step,snapshot){
 const expected=EXPECTED[step];if(!expected)throw new Error('unknown fixture checkpoint '+step);
 if(!snapshot.visibleMatchesLegacy)throw new Error(step+': visible React header differs from authoritative legacy display');
 for(const [key,value] of Object.entries(expected)){
  if(JSON.stringify(snapshot.fixture?.[key])!==JSON.stringify(value))throw new Error(step+': '+key+' expected '+JSON.stringify(value)+' got '+JSON.stringify(snapshot.fixture?.[key]));
 }
 if(CLOSED.has(step)&&snapshot.padOpen)throw new Error(step+': pad must be closed');
 if(!CLOSED.has(step)&&!snapshot.padOpen)throw new Error(step+': pad must remain open');
 return {step,expectedFields:Object.keys(expected),pass:true};
}
module.exports={validateFixtureState,EXPECTED};
