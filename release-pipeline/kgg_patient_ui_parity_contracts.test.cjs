const test=require('node:test'),assert=require('node:assert/strict');
let validate;
try{validate=require('./kgg_patient_ui_parity_contracts.cjs').validateFixtureState}catch(e){if(e.code!=='MODULE_NOT_FOUND')throw e}
const valid=(fixture,extra={})=>({fixture,padOpen:false,visibleMatchesLegacy:true,...extra});
function call(step,state){assert.equal(typeof validate,'function','independent fixture validator missing');return validate(step,state)}
test('independent expected-value validator exists',()=>assert.equal(typeof validate,'function'));
test('equal but wrong values cannot pass pair completion',()=>{
 assert.throws(()=>call('pair-complete',valid({pair1:['99','12']})),/expected/);
 assert.doesNotThrow(()=>call('pair-complete',valid({pair1:['15','12']})));
});
test('cancel may not persist the draft',()=>{
 assert.throws(()=>call('cancelled',valid({pair2:['0','']})),/expected/);
 assert.doesNotThrow(()=>call('cancelled',valid({pair2:['','']})));
});
test('explicit zero remains distinct from unset',()=>{
 assert.throws(()=>call('saved-zero',valid({pair2:['','']})),/expected/);
 assert.doesNotThrow(()=>call('saved-zero',valid({pair2:['0','']})));
});
test('center transfer has its own independent expected pair',()=>{
 assert.throws(()=>call('center-complete',valid({pair3:['25','']})),/expected/);
 assert.doesNotThrow(()=>call('center-complete',valid({pair3:['25','9']})));
});
test('left-side transfer must leave right untouched',()=>{
 assert.throws(()=>call('lr-left',valid({left:['11','8'],right:['11','8']})),/expected/);
 assert.doesNotThrow(()=>call('lr-left',valid({left:['11','8'],right:['','']})));
});
test('seconds-only exercise may not acquire a phantom load',()=>{
 assert.throws(()=>call('seconds-complete',valid({timer:['0','45']})),/expected/);
 assert.doesNotThrow(()=>call('seconds-complete',valid({timer:['','45']})));
});
test('visible React/legacy mismatch is not hidden by matching data stores',()=>{
 assert.throws(()=>call('pair-wdh',valid({pair1:['','']},{padOpen:true,visibleMatchesLegacy:false})),/visible/);
});
test('successful pair must close the NumPad',()=>{
 assert.throws(()=>call('pair-complete',valid({pair1:['15','12']},{padOpen:true})),/pad/);
});
