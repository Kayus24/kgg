# KGG Source Chunk 046

- Source: `kgg-update/index.html`
- Lines: 19321-19740

```html
    const placeholderHeight=Math.max(48,rect.height);
    placeholder.style.height=placeholderHeight+'px';
    /*
      v4b phone drag-position-only:
      v401 still forces phone placeholders to 20px via !important.
      Do not touch layout CSS. Override only this live placeholder inline,
      only in phone layout, so the list keeps the same height reserve as tablet.
    */
    if(isPhoneLayout()){
      placeholder.style.setProperty('height',placeholderHeight+'px','important');
      placeholder.style.setProperty('min-height',placeholderHeight+'px','important');
      placeholder.style.setProperty('padding','0','important');
      placeholder.style.setProperty('box-sizing','border-box','important');
    }
    placeholder.setAttribute('aria-hidden','true');
    card.after(placeholder);
    if(isPhoneLayout()){
      document.body.classList.add('kggPlanCardReordering');
      clearPhoneScrollStateForPlanGesture(520);
    }
    card.classList.remove('reorder-prelift');
    card.classList.add('reorder-lifted');
    if(phoneDrag){
      /*
        v7 phone drag local-list coordinates:
        Do not use position:fixed on phone. Some mobile WebViews resolve fixed
        against transformed/contained ancestors, which moves the lifted card far
        away from the finger. Keep the card absolutely positioned inside #planList
        and calculate left/top in that local coordinate system.
      */
      const anchorX=Number.isFinite(press.pointerOffsetX)?press.pointerOffsetX:(rect.width/2);
      const anchorY=Number.isFinite(press.pointerOffsetY)?press.pointerOffsetY:(rect.height/2);
      const initialX=initialEv&&Number.isFinite(initialEv.clientX)?initialEv.clientX:press.startX;
      const initialY=initialEv&&Number.isFinite(initialEv.clientY)?initialEv.clientY:press.startY;
      const listRect=list.getBoundingClientRect();
      press.phoneListAbsoluteDrag=true;
      press.dragAnchorX=anchorX;
      press.dragAnchorY=anchorY;
      /*
        v8 tablet safety:
        v7 left #planList with inline position:relative after a phone drag.
        That can leak into tablet/orientation mode in the same session.
        Store and restore the exact previous inline value.
      */
      press.listPrevPosition=list.style.getPropertyValue('position');
      press.listPrevPositionPriority=list.style.getPropertyPriority('position');
      list.style.setProperty('position','relative');
      card.style.setProperty('position','absolute','important');
      card.style.setProperty('left',(initialX-anchorX-listRect.left+list.scrollLeft)+'px','important');
      card.style.setProperty('top',(initialY-anchorY-listRect.top+list.scrollTop)+'px','important');
      card.style.setProperty('right','auto','important');
      card.style.setProperty('bottom','auto','important');
      card.style.setProperty('margin','0','important');
      card.style.setProperty('width',rect.width+'px','important');
      card.style.setProperty('transform','translate3d(0,0,0)','important');
      card.style.setProperty('transform-origin',anchorX+'px '+anchorY+'px','important');
      card.style.setProperty('--drag-left','0px');
      card.style.setProperty('--drag-top','0px');
      card.style.setProperty('--drag-y','0px');
    }else{
      card.style.setProperty('--drag-left',(rect.left-fixedOffset.left)+'px');
      card.style.setProperty('--drag-top',(rect.top-fixedOffset.top)+'px');
      card.style.setProperty('--drag-y','0px');
      card.style.width=rect.width+'px';
    }
    list.classList.add('reorder-active');
    press.active=true;
    press.placeholder=placeholder;
    press.startTop=rect.top;
    press.cardHeight=rect.height;
    press.currentIndex=(state.plan||[]).findIndex(ex=>String(ex.localId||ex.id)===press.id);
    press.targetIndex=press.currentIndex;
    state.reorderSuppressClick=true;
    try{press.handle.setPointerCapture&&press.handle.setPointerCapture(press.pointerId);}catch(e){}
    document.removeEventListener('pointermove',press.preMove);
    document.removeEventListener('pointerup',press.preUp);
    document.addEventListener('pointermove',onAnimatedReorderMove,{passive:false});
    document.addEventListener('pointerup',finishAnimatedReorder,{passive:false,once:true});
    document.addEventListener('pointercancel',cancelAnimatedReorder,{passive:false,once:true});
    if(initialEv)onAnimatedReorderMove(initialEv);
  }
  function onAnimatedReorderMove(ev){
    const press=animatedReorder;
    if(!press||!press.active)return;
    clearPhoneScrollStateForPlanGesture(520);
    ev.preventDefault();
    const dy=ev.clientY-press.startY;
    let floatingMid;
    if(press.phoneListAbsoluteDrag){
      const anchorX=Number.isFinite(press.dragAnchorX)?press.dragAnchorX:(Number.isFinite(press.pointerOffsetX)?press.pointerOffsetX:0);
      const anchorY=Number.isFinite(press.dragAnchorY)?press.dragAnchorY:(Number.isFinite(press.pointerOffsetY)?press.pointerOffsetY:0);
      const listRect=press.list.getBoundingClientRect();
      const nextLeft=ev.clientX-anchorX-listRect.left+press.list.scrollLeft;
      const nextTop=ev.clientY-anchorY-listRect.top+press.list.scrollTop;
      press.card.style.setProperty('left',nextLeft+'px','important');
      press.card.style.setProperty('top',nextTop+'px','important');
      press.card.style.setProperty('transform','translate3d(0,0,0)','important');
      press.card.style.setProperty('--drag-y','0px');
      floatingMid=ev.clientY-anchorY+(Number.isFinite(press.cardHeight)?press.cardHeight:press.card.getBoundingClientRect().height)/2;
    }else if(press.phoneAnchoredDrag){
      const anchorX=Number.isFinite(press.pointerOffsetX)?press.pointerOffsetX:0;
      const anchorY=Number.isFinite(press.pointerOffsetY)?press.pointerOffsetY:0;
      const fixedOffset=press.fixedOffset||{left:0,top:0};
      const nextLeft=ev.clientX-anchorX-fixedOffset.left;
      const nextTop=ev.clientY-anchorY-fixedOffset.top;
      press.card.style.setProperty('--drag-left',nextLeft+'px');
      press.card.style.setProperty('--drag-top',nextTop+'px');
      press.card.style.setProperty('--drag-y','0px');
      floatingMid=ev.clientY-anchorY+(Number.isFinite(press.cardHeight)?press.cardHeight:press.card.getBoundingClientRect().height)/2;
    }else{
      press.card.style.setProperty('--drag-y',dy+'px');
      floatingMid=press.startTop+dy+(press.card.getBoundingClientRect().height/2);
    }
    const cards=Array.from(press.list.querySelectorAll('.planCard[data-plan-id]:not(.reorder-lifted)'));
    let target=cards.length;
    for(let i=0;i<cards.length;i++){
      const r=cards[i].getBoundingClientRect();
      if(floatingMid<r.top+r.height/2){target=i;break;}
    }
    press.targetIndex=target;
    const ref=cards[target]||null;
    if(ref)press.list.insertBefore(press.placeholder,ref); else press.list.appendChild(press.placeholder);
    cards.forEach(c=>c.classList.remove('reorder-gap-before','reorder-gap-after'));
    if(ref)ref.classList.add('reorder-gap-before');
    else if(cards.length)cards[cards.length-1].classList.add('reorder-gap-after');
  }
  function finishAnimatedReorder(ev){
    const press=animatedReorder;
    if(!press||!press.active){cleanupAnimatedReorder(false);return;}
    ev.preventDefault();
    const dbAnchor=state.bankOpen&&typeof captureDbScrollAnchor==='function'?captureDbScrollAnchor():null;
    const from=(state.plan||[]).findIndex(ex=>String(ex.localId||ex.id)===press.id);
    let to=Array.from(press.list.children).indexOf(press.placeholder);
    if(from<0){cleanupAnimatedReorder(false);return;}
    if(to>from)to-=1;
    to=Math.max(0,Math.min(state.plan.length-1,to));
    const moved=to!==from;
    if(moved){
      const next=state.plan.slice();
      const item=next.splice(from,1)[0];
      next.splice(to,0,item);
      state.plan=next;
      syncStatePlanToStore('ui_reorder_plan_animated');
      syncTextInputFromPlan('ui_reorder_plan_animated');
      save();
    }
    cleanupAnimatedReorder(true);
    renderPlan();
    if(dbAnchor&&typeof restoreDbScrollAnchor==='function'){
      restoreDbScrollAnchor(dbAnchor);
      setTimeout(()=>restoreDbScrollAnchor(dbAnchor),40);
    }
  }
  function cancelAnimatedReorder(ev){cleanupAnimatedReorder(true);renderPlan();}
  function cleanupAnimatedReorder(suppressClick){
    const press=animatedReorder;
    if(!press)return;
    clearTimeout(press.timer);
    if(press.handle)press.handle.classList.remove('reorder-armed');
    if(press.list)press.list.classList.remove('reorder-active');
    document.body.classList.remove('kggPlanCardReordering');
    clearPhoneScrollStateForPlanGesture(280);
    if(press.card){
      const keepSwipeStyles=press.card.classList.contains('swipe-dragging')||document.body.classList.contains('kggPlanCardSwiping');
      press.card.classList.remove('reorder-lifted','reorder-prelift');
      if(!keepSwipeStyles){
        press.card.style.removeProperty('--drag-left');
        press.card.style.removeProperty('--drag-top');
        press.card.style.removeProperty('--drag-y');
        press.card.style.removeProperty('width');
        press.card.style.removeProperty('position');
        press.card.style.removeProperty('left');
        press.card.style.removeProperty('top');
        press.card.style.removeProperty('right');
        press.card.style.removeProperty('bottom');
        press.card.style.removeProperty('margin');
        press.card.style.removeProperty('transform');
        press.card.style.removeProperty('transform-origin');
      }
    }
    if(press.placeholder&&press.placeholder.parentNode)press.placeholder.parentNode.removeChild(press.placeholder);
    if(press.list){
      if(press.phoneListAbsoluteDrag){
        if(press.listPrevPosition){
          press.list.style.setProperty('position',press.listPrevPosition,press.listPrevPositionPriority||'');
        }else{
          press.list.style.removeProperty('position');
        }
      }
      Array.from(press.list.querySelectorAll('.reorder-gap-before,.reorder-gap-after')).forEach(c=>c.classList.remove('reorder-gap-before','reorder-gap-after'));
    }
    if(press.preMove)document.removeEventListener('pointermove',press.preMove);
    if(press.preUp)document.removeEventListener('pointerup',press.preUp);
    document.removeEventListener('pointermove',onAnimatedReorderMove);
    animatedReorder=null;
    if(suppressClick){state.reorderSuppressClick=true;setTimeout(()=>{state.reorderSuppressClick=false;},350);}
  }

  function restoreRecentPlan(index){
    const item=(state.recent||[])[index];
    if(!item)return;
    state.patient={...(state.patient||{}),...(item.patient||{})};
    state.plan=Array.isArray(item.exercises)?item.exercises.map(ensureUiExerciseShape):[];
    if($('patientName'))$('patientName').value=state.patient.name||'';
    if($('planDate'))$('planDate').value=state.patient.date||new Date().toISOString().slice(0,10);
    if($('therapistName'))$('therapistName').value=state.patient.therapist||'';
    if($('planNotes'))$('planNotes').value=state.patient.notes||'';
    syncStatePlanToStore('ui_restore_recent_plan');
    syncTextInputFromPlan('ui_restore_recent_plan');
    if($('recentList'))$('recentList').classList.add('hidden');
    save();
    render();
  }
  function renderRecent(){
    const el=$('recentList');
    const items=(state.recent||[]).slice(0,5);
    el.innerHTML=items.map((p,i)=>'<div class="notice"><b>'+escapeHtml(p.name||('Plan '+(i+1)))+'</b><br><small>'+((p.exercises||[]).length)+' Übungen'+(p.date?' · '+escapeHtml(String(p.date).slice(0,10)):'')+'</small><br><button class="mutedBtn" data-recent-index="'+i+'" type="button" style="width:100%;margin-top:8px">Plan wieder öffnen</button></div>').join('')||'<div class="notice">Keine Pläne.</div>';
    el.querySelectorAll('[data-recent-index]').forEach(btn=>btn.onclick=()=>restoreRecentPlan(Number(btn.dataset.recentIndex)));
  }
  function defaultPackageName(){const patient=String(state.patient&&state.patient.name||'').trim(); const stamp=new Date().toLocaleDateString('de-DE',{day:'2-digit',month:'2-digit'}); return (patient?patient+' ':'')+'Paket '+stamp;}
  function openPackageSaveModal(){
    if(!(state.plan||[]).length)return;
    const btn=$('savePackageBtn'), input=$('packageNameInput');
    if(btn){btn.classList.remove('packagePulse'); void btn.offsetWidth; btn.classList.add('packagePulse'); setTimeout(()=>btn.classList.remove('packagePulse'),560);}
    if(input)input.value=defaultPackageName();
    $('packageSaveModal').classList.add('open');
    setTimeout(()=>input&&input.focus&&input.focus(),30);
  }
  function closePackageSaveModal(){$('packageSaveModal').classList.remove('open');}
  function confirmPackageSave(){
    const input=$('packageNameInput');
    const name=String(input&&input.value||'').trim();
    const exercises=(state.plan||[]).map(ex=>String(ex&&ex.name||'').trim()).filter(Boolean);
    if(!name||!exercises.length){if(input)input.focus(); return;}
    state.packages=Array.isArray(state.packages)?state.packages:[];
    state.packages.unshift({id:'pkg_'+Date.now(),name,exercises,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),source:'current-plan'});
    save();
    queueNativeExerciseBankSync('package_saved');
    closePackageSaveModal();
    if($('packageList'))$('packageList').classList.remove('hidden');
    render();
  }
  function applyPackageToPlan(packageId){
    const p=(state.packages||[]).find(x=>String(x.id)===String(packageId));
    if(!p)return;
    (p.exercises||[]).forEach(n=>addExercise(search(n,1)[0]||{name:n,sets:3,unit:'Wdh',weightUnit:'kg'}));
  }
  function packageOverlayDescription(pkg){
    const exercises=(pkg&&pkg.exercises||[]).map(x=>String(x||'').trim()).filter(Boolean);
    if(!exercises.length)return 'Noch keine Uebungen in diesem Paket.';
    const listed=exercises.slice(0,4).join(', ');
    return 'Enthaelt '+listed+(exercises.length>4?' und weitere Uebungen.':'.');
  }
  function packageOverlayTags(pkg){
    const exercises=(pkg&&pkg.exercises||[]).filter(Boolean);
    const tags=[exercises.length+' Uebungen'];
    if(pkg&&pkg.source==='current-plan')tags.push('Eigener Plan');
    else tags.push('Paket');
    return tags;
  }
  function renderTabletPackageOverlay(){
    const cards=$('tabletPackageCards');
    if(!cards)return;
    const input=$('tabletPackageSearch');
    const query=compact(input&&input.value||'');
    const packages=(state.packages||[]).filter(pkg=>{
      if(!query)return true;
      const hay=compact([pkg.name,(pkg.exercises||[]).join(' ')].join(' '));
      return hay.includes(query);
    });
    if(!packages.length){cards.innerHTML='<div class="tabletPackageEmpty">Keine passenden Uebungspakete gefunden.</div>';return;}
    cards.innerHTML=packages.map(pkg=>{
      const tags=packageOverlayTags(pkg).map(tag=>'<span>'+escapeHtml(tag)+'</span>').join('');
      return '<button class="tabletPackageCard" type="button" data-tablet-pkg="'+escapeHtml(pkg.id)+'"><span class="tabletPackageIcon" aria-hidden="true">&#128230;</span><span class="tabletPackageBody"><b>'+escapeHtml(pkg.name||'Uebungspaket')+'</b><p>'+escapeHtml(packageOverlayDescription(pkg))+'</p><span class="tabletPackageMeta">'+tags+'</span></span><span class="tabletPackageArrow" aria-hidden="true">›</span></button>';
    }).join('');
    cards.querySelectorAll('[data-tablet-pkg]').forEach(btn=>btn.onclick=()=>applyPackageToPlan(btn.dataset.tabletPkg));
  }
  function renderPackages(){
    const el=$('packageList');
    if(el){
      el.innerHTML=(state.packages||[]).map(p=>'<div class="notice"><b>'+escapeHtml(p.name)+'</b><br><small>'+(p.exercises||[]).map(escapeHtml).join(', ')+'</small><br><button class="mutedBtn" data-pkg="'+p.id+'">Paket in Plan uebernehmen</button></div>').join('');
      el.querySelectorAll('[data-pkg]').forEach(b=>b.onclick=()=>applyPackageToPlan(b.dataset.pkg));
    }
    renderTabletPackageOverlay();
  }
  function sanitizeSharedBankExercise(ex){
    return {
      id:String(ex.id||ex.sourceId||('shared_'+compact(ex.name))).slice(0,80),
      name:String(ex.name||'').trim(),
      aliases:String(ex.aliases||ex.name||'').trim(),
      sets:normalizeSetCount(ex.sets||3),
      unit:String(ex.unit||'Wdh'),
      weightUnit:normalizeLoadUnit(ex.weightUnit||'kg'),
      shared:true,
      createdAt:String(ex.createdAt||ex.updatedAt||new Date().toISOString()),
      updatedAt:String(ex.updatedAt||new Date().toISOString())
    };
  }
  function buildSharedExerciseBankPayload(){
    const exercises=bank.map(sanitizeSharedBankExercise).filter(ex=>ex.name);
    return {kind:'kgg-shared-exercise-bank',version:1,appVersion:VERSION,exportedAt:new Date().toISOString(),exercises};
  }
  function parseSharedExerciseBankPayload(raw){
    const payload=typeof raw==='string'?JSON.parse(raw):raw;
    const exercises=Array.isArray(payload)?payload:(Array.isArray(payload&&payload.exercises)?payload.exercises:(Array.isArray(payload&&payload.exerciseBank)?payload.exerciseBank:[]));
    if(!exercises.length)throw new Error('Keine Übungen im Import gefunden.');
    return exercises.map(sanitizeSharedBankExercise).filter(ex=>ex.name);
  }
  function mergeSharedExerciseBank(raw){
    const incoming=parseSharedExerciseBankPayload(raw);
    let added=0,updated=0;
    incoming.forEach(ex=>{
      const existing=bank.find(item=>compact(item.name)===compact(ex.name));
      if(existing){
        if(syncTimestamp(ex.updatedAt)>=syncTimestamp(existing.updatedAt||existing.createdAt)){
          existing.aliases=ex.aliases||existing.aliases;
          existing.sets=ex.sets||existing.sets;
          existing.unit=ex.unit||existing.unit;
          existing.weightUnit=ex.weightUnit||existing.weightUnit;
          existing.shared=true;
          existing.updatedAt=ex.updatedAt||new Date().toISOString();
          updated+=1;
        }
      }else{
        bank.push({...ex,id:ex.id||('shared_'+Date.now()+'_'+added),custom:true,shared:true});
        added+=1;
      }
      deletedBankIds.delete(String(ex.id||''));
    });
    persistDeletedBankIds();
    persistCustomBank();
    render();
    return {added,updated,total:incoming.length};
  }
  function openSharedBankModal(){
    const text=$('sharedBankText'), status=$('sharedBankStatus');
    if(text)text.value=JSON.stringify(buildSharedExerciseBankPayload(),null,2);
    if(status)status.textContent='Bereit.';
    $('sharedBankModal').classList.add('open');
  }
  function closeSharedBankModal(){$('sharedBankModal').classList.remove('open');}
  async function copySharedBankPayload(){
    const text=$('sharedBankText'), status=$('sharedBankStatus');
    if(!text)return;
    try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text.value); if(status)status.textContent='Export kopiert.'; return;}}catch(err){console.warn('DB-Export konnte nicht kopiert werden:',err);}
    text.focus(); text.select(); if(status)status.textContent='Export markiert.';
  }
  function applySharedBankFromText(){
    const status=$('sharedBankStatus');
    try{const result=mergeSharedExerciseBank($('sharedBankText').value); if(status)status.textContent='Import übernommen: '+result.added+' neu, '+result.updated+' aktualisiert.';}
    catch(err){if(status)status.textContent='Import nicht übernommen: '+(err&&err.message||'unbekannter Fehler');}
  }
  function handleSharedBankFile(ev){
    const file=ev.target.files&&ev.target.files[0];
    ev.target.value='';
    if(!file)return;
    const reader=new FileReader();
    reader.onload=()=>{if($('sharedBankText'))$('sharedBankText').value=String(reader.result||''); if($('sharedBankStatus'))$('sharedBankStatus').textContent='Import geladen.';};
    reader.readAsText(file);
  }
  window.KGGSharedBank={exportPayload:buildSharedExerciseBankPayload,merge:mergeSharedExerciseBank,open:openSharedBankModal};
  let nativeExerciseSyncTimer=null;
  let nativeExerciseSyncApplying=false;
  function nativeExerciseSyncAvailable(){
    return !!(window.KGGNativeSync&&window.KGGNativeSync.available&&typeof window.KGGNativeSync.read==='function'&&typeof window.KGGNativeSync.write==='function');
  }
  function syncTimestamp(value){const t=Date.parse(value||''); return Number.isFinite(t)?t:0;}
  function assertCrossDataSafeSyncDocument(doc){
    const allowedPolicyKeys=new Set(['patients','secrets','debugPayloads','rawData']);
    const blockedKeyPattern=new RegExp(['patient','gemini','api'+'key','api'+'_'+'key','secret','token','raw'+'payload','base64'+'payload','qrraw'].join('|'));
    const blocked=[];
    const visit=(value,path)=>{
      if(!value||typeof value!=='object')return;
      Object.keys(value).forEach(key=>{
        const lower=String(key).toLowerCase();
        const policyKey=(path==='sync.privacy'||path.endsWith('.privacy'))&&allowedPolicyKeys.has(key);
        if(policyKey){
          if(value[key]!==false)blocked.push(path+'.'+key);
        }else if(blockedKeyPattern.test(lower)){
          blocked.push(path+'.'+key);
        }
        visit(value[key],path+'.'+key);
      });
    };
    visit(doc,'sync');
    if(blocked.length)throw new Error('Sync-Safe blockiert geschuetzte Felder: '+blocked.slice(0,3).join(', '));
    return doc;
  }
  function syncSafeOrigin(){
    let deviceId='';
    try{deviceId=syncPairDeviceId();}catch(err){deviceId='web_'+Date.now().toString(36);}
    const config=normalizeNativeSyncFollowConfig(nativeSyncFollowConfig&&nativeSyncFollowConfig()||{});
    const displayName=String(($('therapistName')&&$('therapistName').value)||state.patient.therapist||'KGG Geraet').trim();
    return {deviceId,therapistId:String(config.therapistId||deviceId),displayName,roomId:syncPairRoomId()};
  }
  function syncSafeTombstones(exportedAt){
    return [...deletedBankIds].map(id=>({id:String(id),deleted:true,updatedAt:exportedAt}));
  }
  function sanitizeNativeSyncPackage(pkg){
    return {
      id:String(pkg&&pkg.id||('pkg_'+compact(pkg&&pkg.name||''))).slice(0,96),
      name:String(pkg&&pkg.name||'').trim(),
      exercises:Array.isArray(pkg&&pkg.exercises)?pkg.exercises.map(name=>String(name||'').trim()).filter(Boolean):[],
      createdAt:String(pkg&&pkg.createdAt||new Date().toISOString()),
      updatedAt:String(pkg&&pkg.updatedAt||pkg&&pkg.createdAt||new Date().toISOString()),
      source:String(pkg&&pkg.source||'exercise-package')
    };
  }
  function buildNativeExerciseBankSyncDocument(){
    const exportedAt=new Date().toISOString();
    return assertCrossDataSafeSyncDocument({
      kind:'kgg_cross_data_safe_sync',
      version:2,
      appVersion:VERSION,
      exportedAt,
      roomId:syncPairRoomId(),
      schema:'exercise-bank-packages-v2',
      scopes:['exerciseBank','packages'],
      privacy:{patients:false,secrets:false,debugPayloads:false,rawData:false},
      origin:syncSafeOrigin(),
```
