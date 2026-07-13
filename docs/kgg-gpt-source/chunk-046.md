# KGG Source Chunk 046

- Source: `kgg-update/index.html`
- Lines: 19321-19740

```html
      cleanup();
      if(!swipe.active){resetPlanCardSwipe(card);return;}
      e.preventDefault(); if(e.stopPropagation)e.stopPropagation(); card.dataset.swipeSuppressClickUntil=String(Date.now()+360);
      clearPhoneScrollStateForPlanGesture(520);
      document.body.classList.remove('kggPlanCardSwiping');
      const shouldDelete=Math.abs(swipe.dx)>=threshold();
      if(shouldDelete){
        const dir=swipe.dx<0?-1:1;
        card.classList.add('swipe-removing');
        card.style.transition='transform .18s cubic-bezier(.2,.9,.2,1), opacity .18s ease';
        card.style.setProperty('--kgg-plan-swipe-x',(dir*(card.offsetWidth+96))+'px');
        card.style.transform='translateX(var(--kgg-plan-swipe-x,0px))';
        card.style.opacity='0';
        setTimeout(()=>{document.body.classList.remove('kggPlanCardSwiping');removeExercise(id);},190);
        return;
      }
      card.style.transition='transform .22s cubic-bezier(.2,.9,.2,1), opacity .18s ease, box-shadow .18s ease';
      card.style.setProperty('--kgg-plan-swipe-x','0px');
      card.style.transform='translateX(var(--kgg-plan-swipe-x,0px))';
      card.style.opacity='1';
      setTimeout(()=>resetPlanCardSwipe(card),230);
    };
    const cancel=()=>{
      if(swipe.active){
        clearTimeout(swipe.cancelTimer);
        swipe.cancelTimer=setTimeout(()=>{cleanup();resetPlanCardSwipe(card);},900);
        return;
      }
      cleanup();
      resetPlanCardSwipe(card);
    };
    document.addEventListener('pointermove',move,{passive:false});
    document.addEventListener('pointerup',up,{passive:false,once:true});
    document.addEventListener('pointercancel',cancel,{passive:true,once:true});
  }
  function movePlanExerciseByButton(localId,delta){
    const idx=(state.plan||[]).findIndex(ex=>String(ex.localId||ex.id)===String(localId));
    if(idx<0)return;
    const target=idx+delta;
    if(target<0||target>=state.plan.length)return;
    const next=state.plan.slice();
    const item=next.splice(idx,1)[0];
    next.splice(target,0,item);
    state.plan=next;
    state.sortMenuId=String(item.localId||item.id);
    syncStatePlanToStore('ui_reorder_plan_buttons');
    syncTextInputFromPlan('ui_reorder_plan_buttons');
    save();
    renderPlan();
  }
  let animatedReorder=null;
  function startAnimatedReorderPress(ev){
    if(ev.button!=null && ev.button!==0)return;
    const eventTarget=ev.currentTarget;
    const cardFromTarget=eventTarget&&eventTarget.closest?eventTarget.closest('.planCard'):null;
    const handle=(eventTarget&&eventTarget.matches&&eventTarget.matches('.drag[data-sort-id]'))?eventTarget:(cardFromTarget?cardFromTarget.querySelector('.drag[data-sort-id]'):null);
    const id=String((handle&&handle.dataset&&handle.dataset.sortId)||'');
    const card=(handle&&handle.closest?handle.closest('.planCard'):null)||cardFromTarget;
    const list=$('planList');
    if(!id||!card||!list||state.plan.length<2)return;
    let startX=ev.clientX,startY=ev.clientY;
    const downRect=card.getBoundingClientRect();
    const press={
      id,handle,card,list,startX,startY,pointerId:ev.pointerId,timer:null,active:false,cancelled:false,
      /*
        v5 phone drag anchor:
        keep the lifted card anchored to the exact finger offset captured before
        the prelift CSS transform can change its rect.
      */
      downRect:{
        left:downRect.left,
        top:downRect.top,
        width:downRect.width,
        height:downRect.height
      },
      pointerOffsetX:ev.clientX-downRect.left,
      pointerOffsetY:ev.clientY-downRect.top,
      phoneAnchoredDrag:false,
      fixedOffset:{left:0,top:0}
    };
    animatedReorder=press;
    handle.classList.add('reorder-armed');
    card.classList.add('reorder-prelift');
    press.timer=setTimeout(()=>activateAnimatedReorder(press,ev),100);
    const moveBefore=e=>{
      if(animatedReorder!==press)return;
      const dx=Math.abs(e.clientX-startX),dy=Math.abs(e.clientY-startY);
      if(!press.active && (dx>10 || dy>10)){
        clearTimeout(press.timer);
        press.cancelled=true;
        cleanupAnimatedReorder(false);
      }
    };
    const upBefore=e=>{
      if(animatedReorder!==press)return;
      if(!press.active){clearTimeout(press.timer);cleanupAnimatedReorder(false);}
    };
    press.preMove=moveBefore;
    press.preUp=upBefore;
    document.addEventListener('pointermove',moveBefore,{passive:true});
    document.addEventListener('pointerup',upBefore,{passive:true,once:true});
    document.addEventListener('pointercancel',upBefore,{passive:true,once:true});
  }
  function fixedContainingBlockOffset(el){
    let node=el&&el.parentElement;
    while(node&&node!==document.documentElement){
      const cs=getComputedStyle(node);
      const backdrop=cs.backdropFilter||cs.webkitBackdropFilter||'none';
      const contain=cs.contain||'';
      const willChange=cs.willChange||'';
      const createsFixedBlock=
        cs.transform!=='none'||
        cs.perspective!=='none'||
        cs.filter!=='none'||
        backdrop!=='none'||
        contain.includes('paint')||
        contain.includes('layout')||
        willChange.includes('transform');
      if(createsFixedBlock){
        const r=node.getBoundingClientRect();
        return {left:r.left,top:r.top};
      }
      node=node.parentElement;
    }
    return {left:0,top:0};
  }
  function activateAnimatedReorder(press,initialEv){
    if(animatedReorder!==press||press.cancelled)return;
    const card=press.card,list=press.list;
    const phoneDrag=isPhoneLayout();
    /*
      v5 phone drag anchor:
      On phone, use the card rect captured at pointerdown, not the transformed
      prelift rect after the 100ms hold. This prevents the lifted card from
      jumping away from the finger at activation.
    */
    const liveRect=card.getBoundingClientRect();
    const rect=(phoneDrag&&press.downRect)?press.downRect:liveRect;
    const fixedOffset=fixedContainingBlockOffset(card);
    press.fixedOffset=fixedOffset;
    press.phoneAnchoredDrag=!!phoneDrag;
    const placeholder=document.createElement('div');
    placeholder.className='planCard reorder-placeholder';
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
```
