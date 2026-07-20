# KGG Source Chunk 045

- Source: `kgg-update/src` modular source
- Lines: 18901-19320

```html
    if(!media)return '';
    return '<span class="bankThumb bankThumbFallback" data-bank-thumb-id="'+escapeHtml(media.id)+'" title="Bild vorhanden" aria-hidden="true"></span>';
  }
  async function hydrateBankThumbnails(root){
    if(!root)return;
    Array.from(root.querySelectorAll('[data-bank-thumb-id]')).forEach(async node=>{
      const id=String(node.getAttribute('data-bank-thumb-id')||'');
      if(!id)return;
      try{
        const owner=bank.find(ex=>ensureExerciseMediaList(ex).some(item=>String(item&&item.id)===id));
        const media=owner&&ensureExerciseMediaList(owner).find(item=>String(item&&item.id)===id);
        if(!media)throw new Error('Kein Bildmanifest');
        const record=await getEncryptedMediaBlob(id);
        if(!node.isConnected)return;
        if(!record||!record.blob)throw new Error('Lokales Bild fehlt');
        const imageBlob=await patientDecryptMedia(media,record.blob);
        if(!node.isConnected)return;
        if(node._kggThumbUrl)URL.revokeObjectURL(node._kggThumbUrl);
        const url=URL.createObjectURL(imageBlob);
        node._kggThumbUrl=url;
        node.classList.remove('bankThumbFallback');
        node.innerHTML='<img src="'+url+'" alt="">';
        setTimeout(()=>{try{if(node._kggThumbUrl===url){URL.revokeObjectURL(url);node._kggThumbUrl='';}}catch(e){}},60000);
      }catch(err){
        if(node.isConnected){node.classList.add('bankThumbFallback');node.innerHTML='';}
      }
    });
  }
  function renderBank(text){const c=$('bankContent'); const btn=$('bankToggle'); const area=$('bankArea'); const effectiveOpen=state.bankOpen||isTabletLayout(); const shouldHideToggle=!effectiveOpen&&!!text; btn.classList.toggle('hidden',shouldHideToggle); btn.classList.toggle('dbMascotDock',effectiveOpen); const caret=effectiveOpen?'▾':'▸'; btn.innerHTML='<span class="dbToggleMain"><span class="dbMascotBubble" aria-hidden="true"><span class="dbCaret">'+caret+'</span><span class="dbMascot">🏋️</span></span><span class="dbToggleText">Übungsdatenbank</span></span>'; btn.setAttribute('aria-label',effectiveOpen?'Übungsdatenbank schließen':'Übungsdatenbank öffnen'); c.classList.toggle('hidden',!effectiveOpen); area.classList.toggle('bankOpen',effectiveOpen); area.classList.toggle('alphaBankOpen',effectiveOpen&&!text); area.classList.toggle('searchBankOpen',effectiveOpen&&!!text); if(!effectiveOpen){c.innerHTML=''; return;} const matches=text?search(text,8):allAlpha(); const list=text?fillBankListWithFallback(matches,8):matches; const fallbackOnly=!!text&&matches.length===0; let rows=list.map((ex,i)=>{const letter=bankLetterForName(ex.name); return '<div class="bankRow" data-letter="'+letter+'" data-bank-index="'+i+'"><button class="iconBtn bankAddBtn" data-add="'+ex.id+'" aria-label="Übung übernehmen">'+bankCardThumbnailHtml(ex)+'<span class="bankText"><b>'+escapeHtml(ex.name)+'</b><small>'+(ex.unit||'Wdh')+' · '+(ex.weightUnit||'kg')+'</small></span></button><button class="iconBtn" data-edit="'+ex.id+'" aria-label="Übung bearbeiten">⚙️</button></div>';}).join(''); if(text){const label=fallbackOnly?'Alternative Treffer':'Beste Treffer'; c.innerHTML='<div class="bankLabel">'+label+'</div><div class="bankRows">'+rows+'</div>';} else {const availableLetters=new Set(list.map(ex=>bankLetterForName(ex.name))); c.innerHTML='<div class="bankWithAz"><nav class="az" aria-label="A-Z Sprungleiste">'+'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').map(l=>'<button type="button" data-jump="'+l+'" class="'+(availableLetters.has(l)?'':'az-empty')+'">'+l+'</button>').join('')+'</nav><div class="bankRows">'+rows+'</div></div>'; bindAzScrollrad(c);} hydrateBankThumbnails(c); c.querySelectorAll('[data-add]').forEach(b=>{preventButtonFocusSteal(b); b.onclick=ev=>{ev.preventDefault();ev.stopPropagation();if(Date.now()<bankSwipeSuppressClickUntil)return; applySelectedExerciseToText(bank.find(x=>x.id===b.dataset.add),{keepFocus:!isPhoneLayout()||!document.body.classList.contains('kggPhoneDbBrowseMode')});};}); c.querySelectorAll('[data-edit]').forEach(b=>b.onclick=ev=>{if(Date.now()<bankSwipeSuppressClickUntil){ev.preventDefault();ev.stopPropagation();return;} openEditor(bank.find(x=>x.id===b.dataset.edit));});}
  function bindBankSwipeDelete(container){
    if(!container)return;
    container.querySelectorAll('.bankRow').forEach(row=>{
      if(row.dataset.bankSwipeBound==='1')return;
      const btn=row.querySelector('[data-add],[data-edit]');
      const id=btn&&(btn.dataset.add||btn.dataset.edit);
      if(!id)return;
      row.dataset.bankId=id;
      row.dataset.bankSwipeBound='1';
      row.addEventListener('click',ev=>{if(Date.now()<bankSwipeSuppressClickUntil){ev.preventDefault();ev.stopPropagation();}},true);
      row.addEventListener('pointerdown',startBankRowSwipeDelete,{passive:true});
    });
  }
  function resetBankRowSwipe(row){
    if(!row)return;
    row.classList.remove('bank-swipe-dragging','bank-swipe-armed','bank-swipe-left','bank-swipe-right');
    row.style.removeProperty('transform');
    row.style.removeProperty('opacity');
    row.style.removeProperty('transition');
    row.style.removeProperty('--bank-swipe-strength');
  }
  function startBankRowSwipeDelete(ev){
    if(ev.button!=null&&ev.button!==0)return;
    if(ev.target&&ev.target.closest&&ev.target.closest('[data-edit],input,textarea,select,a'))return;
    const row=ev.currentTarget;
    const id=row&&row.dataset&&row.dataset.bankId;
    if(!row||!id)return;
    const startX=ev.clientX,startY=ev.clientY;
    const swipe={row,id,startX,startY,active:false,dx:0,pointerId:ev.pointerId};
    const threshold=()=>Math.min(128,Math.max(74,row.offsetWidth*0.34));
    const cleanup=()=>{document.removeEventListener('pointermove',move);document.removeEventListener('pointerup',up);document.removeEventListener('pointercancel',cancel);};
    const move=e=>{
      const dx=e.clientX-startX,dy=e.clientY-startY;
      if(!swipe.active){
        if(Math.abs(dy)>10&&Math.abs(dy)>Math.abs(dx)*1.2){cleanup();return;}
        if(Math.abs(dx)<12||Math.abs(dx)<Math.abs(dy)*1.25)return;
        swipe.active=true;
        row.classList.add('bank-swipe-dragging');
        try{row.setPointerCapture&&row.setPointerCapture(swipe.pointerId);}catch(err){}
      }
      if(!swipe.active)return;
      e.preventDefault();
      const max=row.offsetWidth*0.86;
      swipe.dx=Math.max(-max,Math.min(max,dx));
      const strength=Math.min(1,Math.abs(swipe.dx)/threshold());
      row.classList.toggle('bank-swipe-left',swipe.dx<0);
      row.classList.toggle('bank-swipe-right',swipe.dx>0);
      row.classList.toggle('bank-swipe-armed',Math.abs(swipe.dx)>=threshold());
      row.style.setProperty('--bank-swipe-strength',String(strength));
      row.style.transform='translateX('+swipe.dx+'px)';
      row.style.opacity=String(1-strength*0.12);
    };
    const up=e=>{
      cleanup();
      if(!swipe.active){resetBankRowSwipe(row);return;}
      e.preventDefault();
      bankSwipeSuppressClickUntil=Date.now()+380;
      const shouldAsk=Math.abs(swipe.dx)>=threshold();
      row.style.transition='transform .2s cubic-bezier(.2,.9,.2,1), opacity .16s ease, box-shadow .16s ease';
      row.style.transform='translateX(0)';
      row.style.opacity='1';
      setTimeout(()=>{resetBankRowSwipe(row); if(shouldAsk)openBankDeleteModal(id);},210);
    };
    const cancel=()=>{cleanup(); if(swipe.active){row.style.transition='transform .18s ease, opacity .18s ease';row.style.transform='translateX(0)';row.style.opacity='1';setTimeout(()=>resetBankRowSwipe(row),190);}else resetBankRowSwipe(row);};
    document.addEventListener('pointermove',move,{passive:false});
    document.addEventListener('pointerup',up,{passive:false,once:true});
    document.addEventListener('pointercancel',cancel,{passive:true,once:true});
  }
  function scanSetSummaryForPlanCard(ex){
    const sets=Array.isArray(ex&&ex.scanSets)?ex.scanSets:[];
    if(!sets.length)return '';
    const metricUnit=ex&&ex.metricUnit||ex&&ex.unit||measureUnitLabel(ex&&ex.measure);
    const loadUnit=normalizeLoadUnit(ex&&ex.weightUnit||ex&&ex.loadUnit||'kg');
    const isTime=/zeit|sek|sec|min|time/i.test(metricUnit)||/keine/i.test(loadUnit);
    return sets.slice(0,3).map((set,i)=>{
      if(set&&set.li||set&&set.re){
        const li=set.li||{}, re=set.re||{};
        const liText=(li.metric?li.metric+' '+metricUnit:'')+(li.load?' @ '+li.load+' '+loadUnit:'');
        const reText=(re.metric?re.metric+' '+metricUnit:'')+(re.load?' @ '+re.load+' '+loadUnit:'');
        return 'S'+(i+1)+': Li '+(liText||'-')+' / Re '+(reText||'-')+(set.pain?' · Schmerz '+set.pain+'/10':'');
      }
      if(isTime)return 'S'+(i+1)+': '+(set&&set.metric||'-')+' '+metricUnit+(set&&set.pain?' · Schmerz '+set.pain+'/10':'');
      return 'S'+(i+1)+': '+(set&&set.metric||'-')+' '+metricUnit+(set&&set.load?' @ '+set.load+' '+loadUnit:'')+(set&&set.pain?' · Schmerz '+set.pain+'/10':'');
    }).join(' · ');
  }
  function exerciseMeta(ex){
    const scanSummary=scanSetSummaryForPlanCard(ex);
    if(scanSummary)return scanSummary;
    const parts=[];
    parts.push(normalizeSetCount(ex&&ex.sets||3)+' Sätze');
    parts.push(sideModeLabel(ex&&ex.side));
    const loadUnit=normalizeLoadUnit(ex&&ex.weightUnit||ex&&ex.loadUnit||'kg');
    const metricUnit=ex&&ex.unit||ex&&ex.metricUnit||measureUnitLabel(ex&&ex.measure);
    parts.push(loadUnit);
    parts.push(metricUnit||'Wdh');
    return parts.filter(Boolean).join(' · ');
  }
  function planCardSourceText(ex){
    if(ex&&ex.scanImported)return ex.scanSource||'Scan übernommen';
    const raw=String(ex&&ex.rawText||'').trim();
    const name=String(ex&&ex.name||'').trim();
    if(raw&&compact(raw)!==compact(name))return raw;
    return name||String(ex&&ex.source||ex&&ex.sourceId||ex&&ex.bankId||'').trim();
  }
  function planCardBadgesHtml(ex){
    const mediaCount=ensureExerciseMediaList(ex).length;
    const bits=[];
    if(mediaCount)bits.push('<span class="planBadge media">🖼 Medien</span>');
    if(ex&&ex.pendingNew)bits.push('<span class="planBadge new">neu</span>');
    else if(ex&&ex.needsReview)bits.push('<span class="planBadge review">prüfen</span>');
    if(ex&&ex.liveDraft)bits.push('<span class="planBadge live">live</span>');
    return bits.join('');
  }
  function planCardThumbnailHtml(ex){
    const media=ensureExerciseMediaList(ex).find(item=>item&&item.type==='image'&&item.id);
    if(!media)return '';
    return '<span class="planThumb planThumbFallback" data-plan-thumb-id="'+escapeHtml(media.id)+'" title="Bild vorhanden" aria-hidden="true"></span>';
  }
  function planCardSourceText(ex){
    return '';
  }
  function planCardBadgesHtml(ex){
    const mediaCount=ensureExerciseMediaList(ex).length;
    const bits=[];
    if(mediaCount)bits.push('<span class="planBadge media">Bild</span>');
    if(ex&&ex.liveDraft)bits.push('<span class="planBadge live">Vorschau</span>');
    else if(ex&&ex.pendingNew)bits.push('<span class="planBadge new">neu</span>');
    else if(ex&&ex.needsReview)bits.push('<span class="planBadge review">pruefen</span>');
    return bits.join('');
  }
  async function hydratePlanThumbnails(root){
    if(!root)return;
    Array.from(root.querySelectorAll('[data-plan-thumb-id]')).forEach(async node=>{
      const id=String(node.getAttribute('data-plan-thumb-id')||'');
      if(!id)return;
      try{
        const owner=(state.plan||[]).find(ex=>ensureExerciseMediaList(ex).some(item=>String(item&&item.id)===id));
        const media=owner&&ensureExerciseMediaList(owner).find(item=>String(item&&item.id)===id);
        if(!media)throw new Error('Kein Bildmanifest');
        const record=await getEncryptedMediaBlob(id);
        if(!node.isConnected)return;
        if(!record||!record.blob)throw new Error('Lokales Bild fehlt');
        const imageBlob=await patientDecryptMedia(media,record.blob);
        if(!node.isConnected)return;
        if(node._kggThumbUrl)URL.revokeObjectURL(node._kggThumbUrl);
        const url=URL.createObjectURL(imageBlob);
        node._kggThumbUrl=url;
        node.classList.remove('planThumbFallback');
        node.innerHTML='<img src="'+url+'" alt="">';
        setTimeout(()=>{try{if(node._kggThumbUrl===url){URL.revokeObjectURL(url);node._kggThumbUrl='';}}catch(e){}},60000);
      }catch(err){
        if(node.isConnected){node.classList.add('planThumbFallback');node.innerHTML='';}
      }
    });
  }
  function scanInboxJobs(){try{return (typeof scanState!=='undefined'&&Array.isArray(scanState.jobs))?scanState.jobs:[];}catch(err){return [];}}
  function updateToggleCarets(){
    const baseBtn=$('baseToggle');
    const baseFields=$('baseFields');
    if(baseBtn){
      const open=!!(baseFields&&!baseFields.classList.contains('hidden'));
      const label=baseBtn.querySelector('span:first-child');
      if(label)label.textContent=(open?'▼':'▶')+' 👤 Basisdaten';
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
```
