# KGG Source Chunk 045

- Source: `kgg-update/index.html`
- Lines: 18901-19320

```html
      baseBtn.setAttribute('aria-expanded',open?'true':'false');
    }
    const currentToggle=$('currentPlanToggle');
    if(currentToggle && !currentToggle.hasAttribute('aria-expanded'))currentToggle.setAttribute('aria-expanded','false');
    const scannedToggle=$('scannedPlansToggle');
    if(scannedToggle && !scannedToggle.hasAttribute('aria-expanded'))scannedToggle.setAttribute('aria-expanded','false');
  }
  function setTabletAnchorActiveClasses(){
    const configs=[
      ['base','baseToggle','baseFields'],
      ['recent','recentToggle','recentList'],
      ['package','packageToggle','packageList']
    ];
    configs.forEach(([kind,anchorId,panelId])=>{
      const anchor=$(anchorId), panel=$(panelId);
      const active=!!(isTabletLayout()&&panel&&!panel.classList.contains('hidden')&&tabletOverlayState.kind===kind);
      if(anchor)anchor.classList.toggle('kggOverlayAnchorActive',active);
    });
  }
  function syncScannedPlansMobileDock(){
    const block=$('scannedPlansBlock'), dock=$('mobileScannedPlansDock'), stack=$('rightPlanStack');
    if(!block||!dock||!stack)return;
    const mobile=!isTabletLayout();
    if(mobile){
      if(block.parentNode!==dock)dock.appendChild(block);
      dock.classList.toggle('hidden',block.classList.contains('hidden'));
    }else{
      if(block.parentNode!==stack)stack.appendChild(block);
      dock.classList.add('hidden');
    }
  }
  function setRightPlanPanel(kind,reason){
    state.scanPanelOpen=kind==='scanned'?'scanned':'plan';
    try{save();}catch(err){}
    render();
  }
  function scanDecisionMarkup(kind){
    if(!scanState.decision)return '';
    const cls=kind==='inbox'?'scanInboxDecision':'scanDecision';
    return '<div class="'+cls+'"><h3>Foto hinzugef&uuml;gt</h3><p class="notice">Was kommt als N&auml;chstes?</p><div class="scanDecisionBtns scanDecisionRepeatSource"><button type="button" class="scanRepeatBtn" onclick="window.KGGScan.repeatSource(\'page\')">+ weitere Seite zu diesem Plan</button><button type="button" class="scanRepeatBtn" onclick="window.KGGScan.repeatSource(\'plan\')">+ weiterer Plan / Patient</button><button type="button" class="primary scanFinishBtn" onclick="window.KGGScan.start()">Fertig</button></div></div>';
  }
  function scanInboxCardHtml(job,index){
    const resultText=scanResultToCopyText(job)||'Noch nicht ausgelesen.';
    const quality=job.result&&job.result.quality||{};
    const warn=[...(job.warnings||[]),...((quality.warnings)||[])];
    const cls=job.result?(quality.ok===false?'warn':'good'):(warn.length?'warn':'');
    const typeLabel=job.type==='qr'?'QR-Plan':'Papierplan';
    const title=escapeHtml(job.short||job.label||('Plan '+(index+1)));
    const meta=escapeHtml(typeLabel+' · '+(job.pages&&job.pages.length||0)+' Bild(er)');
    return '<div class="scanInboxCard '+cls+'" data-scan-index="'+index+'">'+
      '<button type="button" class="scanInboxRemoveTop" onclick="window.KGGScan.removeJob('+index+')" aria-label="Scan-Ergebnis entfernen">×</button>'+
      '<div class="scanInboxHead"><div><b>'+title+'</b><small>'+meta+'</small></div></div>'+
      '<textarea id="kggScanInboxField'+index+'" class="scanInboxText" readonly>'+escapeHtml(resultText)+'</textarea>'+
      (warn.length?'<div class="scanWarning">Prüfen: '+escapeHtml(warn.join(' · '))+'</div>':'')+
      '<div class="scanInboxActions">'+
        '<button type="button" class="mutedBtn" onclick="window.KGGScan.copyResult('+index+')">kopieren</button>'+
        '<button type="button" class="primary" onclick="window.KGGScan.applyResult('+index+')">weiter bearbeiten</button>'+
      '</div></div>';
  }
  function renderScannedPlansInbox(){
    const block=$('scannedPlansBlock'), list=$('scannedPlansList'), count=$('scannedPlansCount'), right=$('rightPlanStack');
    if(!block||!list)return;
    const jobs=scanInboxJobs();
    const hasScan=jobs.length>0;
    block.classList.toggle('hidden',!hasScan);
    const scanExpanded=hasScan&&state.scanPanelOpen==='scanned';
    block.classList.toggle('collapsed',hasScan&&!scanExpanded);
    if(count)count.textContent=hasScan?(jobs.length+' Scan'+(jobs.length===1?'':'s')):'';
    if(!hasScan){list.innerHTML=''; updateToggleCarets(); syncScannedPlansMobileDock(); return;}
    list.innerHTML=jobs.map(scanInboxCardHtml).join('');
    const toggle=$('scannedPlansToggle');
    if(toggle){toggle.onclick=()=>setRightPlanPanel('scanned','ui_open_scanned_plans'); toggle.setAttribute('aria-expanded',scanExpanded?'true':'false');}
    updateToggleCarets();
    syncScannedPlansMobileDock();
  }
  function renderPlan(){
    syncStoreToStatePlan('ui_render_plan');
    syncScannedPlansMobileDock();
    const block=$('currentPlanBlock'), list=$('planList'), right=$('rightPlanStack');
    const jobs=scanInboxJobs();
    const hasScan=jobs.length>0;
    const hasPlan=state.plan.length>0;
    const mobileDock=!isTabletLayout();
    if(!state.scanPanelOpen)state.scanPanelOpen=hasScan&&!hasPlan?'scanned':'plan';
    if(hasScan&&state.scanPanelOpen!=='plan')state.scanPanelOpen='scanned';
    const scanOpen=hasScan&&state.scanPanelOpen==='scanned';
    const planOpen=mobileDock?hasPlan:!scanOpen;
    if(right){
      right.classList.toggle('hidden',mobileDock?!hasPlan:!(hasPlan||hasScan));
      right.classList.toggle('scanOpen',scanOpen);
      right.classList.toggle('planOpen',planOpen);
    }
    const createPanel=$('createPanel');
    if(createPanel){
      createPanel.classList.toggle('scanPanelOpen',!!scanOpen);
      createPanel.classList.toggle('planPanelOpen',!!(planOpen&&(hasPlan||hasScan)));
    }
    if(block){
      block.classList.toggle('hidden',!hasPlan);
      block.classList.toggle('collapsed',hasPlan&&!planOpen);
    }
    const planCount=$('currentPlanCount');
    if(planCount){
      const planInfo=hasPlan?(state.plan.length+' Übung'+(state.plan.length===1?'':'en')):'';
      planCount.textContent=planInfo;
    }
    const planToggle=$('currentPlanToggle');
    if(planToggle){
      const planToggleLabel=planToggle.querySelector('span');
      if(planToggleLabel)planToggleLabel.textContent='Übungen im Plan';
      planToggle.onclick=()=>setRightPlanPanel('plan','ui_open_current_plan');
      planToggle.setAttribute('aria-expanded',(hasPlan&&planOpen)?'true':'false');
    }
    if(list){
      list.innerHTML=state.plan.map((ex,i)=>{
        const id=escapeHtml(ex.localId||ex.id);
        const classes=['planCard'];
        if(ensureExerciseMediaList(ex).length)classes.push('has-media');
        if(ex.liveDraft)classes.push('is-live-draft');
        if(ex.pendingNew)classes.push('is-new');
        else if(ex.needsReview)classes.push('is-review');
        const sourceHtml='';
        const thumbnailHtml=planCardThumbnailHtml(ex);
        return '<div class="'+classes.join(' ')+'" data-plan-id="'+id+'">'+
          '<div class="planMain">'+
            '<button class="drag" data-sort-id="'+id+'" type="button" aria-label="Übung verschieben">⠿</button>'+
            thumbnailHtml+
            '<span class="planText">'+
              '<b><span class="planIndex">'+(i+1)+'.</span> <span class="planName">'+escapeHtml(ex.name)+'</span> <span class="planBadges">'+planCardBadgesHtml(ex)+'</span></b>'+
              '<small class="planMetaLine">'+escapeHtml(exerciseMeta(ex))+'</small>'+
              sourceHtml+
            '</span>'+
          '</div>'+
          '<div class="planCardActions">'+
            '<button class="iconBtn" data-planedit="'+id+'" aria-label="Übung bearbeiten">⚙️</button>'+
            '<button class="iconBtn danger planDeleteBtn" data-del="'+id+'" aria-label="Übung löschen">×</button>'+
          '</div>'+
        '</div>';
      }).join('');
      list.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>removeExercise(b.dataset.del));
      list.querySelectorAll('[data-planedit]').forEach(b=>b.onclick=()=>openEditor(state.plan.find(x=>(x.localId||x.id)===b.dataset.planedit)));
      bindPlanSwipeDelete(list);
      bindPlanReorderButtons(list);
      hydratePlanThumbnails(list);
    }
    renderScannedPlansInbox();
  }

  function bindPlanReorderButtons(list){
    if(!list)return;
    list.querySelectorAll('.drag[data-sort-id]').forEach(handle=>{
      handle.onclick=ev=>{
        ev.preventDefault();
        ev.stopPropagation();
        if(state.reorderSuppressClick)state.reorderSuppressClick=false;
      };
      handle.addEventListener('pointerdown',startAnimatedReorderPress,{passive:false});
    });
    list.querySelectorAll('.planCard[data-plan-id]').forEach(card=>{
      if(card.dataset.tabletCardReorderBound==='1')return;
      card.dataset.tabletCardReorderBound='1';
      card.addEventListener('pointerdown',ev=>{
        if(!isTabletLayout())return;
        if(ev.button!=null&&ev.button!==0)return;
        if(animatedReorder)return;
        const target=ev.target;
        if(target&&target.closest&&target.closest('button,input,textarea,select,a,.planCardActions,.drag'))return;
        const startX=ev.clientX,startY=ev.clientY,pointerId=ev.pointerId;
        let cancelled=false;
        const cleanup=()=>{
          document.removeEventListener('pointermove',moveBefore);
          document.removeEventListener('pointerup',upBefore);
          document.removeEventListener('pointercancel',upBefore);
        };
        const moveBefore=e=>{
          if(e.pointerId!==pointerId)return;
          const dx=Math.abs(e.clientX-startX),dy=Math.abs(e.clientY-startY);
          if(dx>10||dy>10){
            cancelled=true;
            clearTimeout(timer);
            cleanup();
          }
        };
        const upBefore=e=>{
          if(e.pointerId!==pointerId)return;
          cancelled=true;
          clearTimeout(timer);
          cleanup();
        };
        const timer=setTimeout(()=>{
          cleanup();
          if(cancelled||animatedReorder)return;
          startAnimatedReorderPress({
            button:0,
            currentTarget:card,
            target:target,
            clientX:startX,
            clientY:startY,
            pointerId:pointerId,
            preventDefault:function(){},
            stopPropagation:function(){}
          });
        },140);
        document.addEventListener('pointermove',moveBefore,{passive:true});
        document.addEventListener('pointerup',upBefore,{passive:true});
        document.addEventListener('pointercancel',upBefore,{passive:true});
      },{passive:false});
    });
  }
  function bindPlanSwipeDelete(list){
    if(!list)return;
    list.querySelectorAll('.planCard[data-plan-id]').forEach(card=>{
      if(card.dataset.swipeDeleteBound==='1')return;
      card.dataset.swipeDeleteBound='1';
      card.addEventListener('pointerdown',startPlanCardSwipeDelete,{passive:false});
      card.addEventListener('click',ev=>{
        if(Number(card.dataset.swipeSuppressClickUntil||0)>Date.now()){
          ev.preventDefault();
          ev.stopPropagation();
        }
      },true);
    });
  }
  function resetPlanCardSwipe(card){
    if(!card)return;
    card.classList.remove('swipe-dragging','swipe-armed','swipe-left','swipe-right','swipe-removing');
    document.body.classList.remove('kggPlanCardSwiping');
    card.style.removeProperty('transform');
    card.style.removeProperty('opacity');
    card.style.removeProperty('transition');
    card.style.removeProperty('--swipe-strength');
    card.style.removeProperty('--kgg-plan-swipe-x');
  }
  function startPlanCardSwipeDelete(ev){
    if(ev.button!=null&&ev.button!==0)return;
    const pendingTabletReorder=(animatedReorder&&isTabletLayout()&&animatedReorder.card===ev.currentTarget&&!animatedReorder.active)?animatedReorder:null;
    if(animatedReorder&&!pendingTabletReorder)return;
    const interactiveTarget=ev.target&&ev.target.closest?ev.target.closest('button,input,textarea,select,a'):null;
    const actionSwipeTarget=interactiveTarget&&interactiveTarget.closest&&interactiveTarget.closest('.planCardActions');
    if(interactiveTarget&&!actionSwipeTarget)return;
    const card=ev.currentTarget;
    const id=card&&card.dataset&&card.dataset.planId;
    if(!card||!id)return;
    const startX=ev.clientX,startY=ev.clientY;
    const swipe={card,id,startX,startY,active:false,dx:0,pointerId:ev.pointerId,cancelTimer:null};
    const threshold=()=>Math.min(132,Math.max(78,card.offsetWidth*0.34));
    const cleanup=()=>{clearTimeout(swipe.cancelTimer);document.removeEventListener('pointermove',move);document.removeEventListener('pointerup',up);document.removeEventListener('pointercancel',cancel);};
    const move=e=>{
      const dx=e.clientX-startX,dy=e.clientY-startY;
      if(!swipe.active){
        if(Math.abs(dy)>10&&Math.abs(dy)>Math.abs(dx)*1.2){cleanup();return;}
        if(Math.abs(dx)<12||Math.abs(dx)<Math.abs(dy)*1.25)return;
        if(pendingTabletReorder&&animatedReorder===pendingTabletReorder){
          clearTimeout(pendingTabletReorder.timer);
          cleanupAnimatedReorder(false);
        }
        swipe.active=true;
        document.body.classList.add('kggPlanCardSwiping');
        clearPhoneScrollStateForPlanGesture(420);
        card.classList.add('swipe-dragging');
        try{card.setPointerCapture&&card.setPointerCapture(swipe.pointerId);}catch(err){}
      }
      if(!swipe.active)return;
      clearPhoneScrollStateForPlanGesture(420);
      e.preventDefault(); if(e.stopPropagation)e.stopPropagation();
      const max=card.offsetWidth*0.86;
      swipe.dx=Math.max(-max,Math.min(max,dx));
      const strength=Math.min(1,Math.abs(swipe.dx)/threshold());
      card.classList.toggle('swipe-left',swipe.dx<0);
      card.classList.toggle('swipe-right',swipe.dx>0);
      card.classList.toggle('swipe-armed',Math.abs(swipe.dx)>=threshold());
      card.style.setProperty('--swipe-strength',String(strength));
      card.style.setProperty('--kgg-plan-swipe-x',swipe.dx+'px');
      card.style.transform='translateX(var(--kgg-plan-swipe-x,0px))';
      card.style.opacity=String(1-strength*0.16);
    };
    const up=e=>{
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
```
