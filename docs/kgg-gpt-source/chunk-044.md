# KGG Source Chunk 044

- Source: `kgg-update/index.html`
- Lines: 18481-18900

```html
    const after=value.slice(pos);
    const lastDelimiter=Math.max(before.lastIndexOf(','),before.lastIndexOf(';'),before.lastIndexOf('\n'));
    const nextOffsets=[after.indexOf(','),after.indexOf(';'),after.indexOf('\n')].filter(i=>i>=0);
    const nextDelimiter=nextOffsets.length?pos+Math.min.apply(null,nextOffsets):value.length;
    const segment=value.slice(lastDelimiter+1,nextDelimiter).trim();
    return hasSearchLetters(segment)?segment:'';
  }
  function isLandscapeTabletViewport(){
    return !!(window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047&&
      typeof window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive==='function'&&
      window.KGG_LANDSCAPE_TABLET_VIEWPORT_V047.isActive());
  }
  function isTabletLayout(){return !!((window.matchMedia&&window.matchMedia('(min-width:760px)').matches)||isLandscapeTabletViewport());}
  let tabletSoftKeyboardBaseHeight=0;
  function isKeyboardRelevantField(el){
    if(!el||el.closest&&el.closest('.modal'))return false;
    return /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName||'');
  }
  function updateTabletSoftKeyboardLayout(){
    const app=document.querySelector('.app');
    if(!app)return;
    const vv=window.visualViewport||null;
    const visibleHeight=vv?vv.height:window.innerHeight;
    const roundedHeight=Math.max(320,Math.round(visibleHeight||window.innerHeight||640));
    document.documentElement.style.setProperty('--kgg-visual-vh',roundedHeight+'px');
    const focused=isKeyboardRelevantField(document.activeElement);
    if(!focused){
      tabletSoftKeyboardBaseHeight=Math.max(tabletSoftKeyboardBaseHeight,roundedHeight,window.innerHeight||0);
    }
    if(!tabletSoftKeyboardBaseHeight)tabletSoftKeyboardBaseHeight=Math.max(roundedHeight,window.innerHeight||0);
    const keyboardOpen=isTabletLayout()&&focused&&(tabletSoftKeyboardBaseHeight-roundedHeight>120);
    app.classList.toggle('softKeyboard',keyboardOpen);
    document.body.classList.toggle('softKeyboard',keyboardOpen);
  }
  function initTabletSoftKeyboardLayout(){
    const schedule=()=>requestAnimationFrame(updateTabletSoftKeyboardLayout);
    updateTabletSoftKeyboardLayout();
    window.addEventListener('resize',schedule);
    window.addEventListener('orientationchange',()=>{tabletSoftKeyboardBaseHeight=0; schedule();});
    document.addEventListener('focusin',schedule);
    document.addEventListener('focusout',()=>setTimeout(updateTabletSoftKeyboardLayout,80));
    if(window.visualViewport){
      window.visualViewport.addEventListener('resize',schedule);
      window.visualViewport.addEventListener('scroll',()=>{if(!isPhoneLayout())schedule();});
    }
  }
  function isPhoneLayout(){return !!(window.matchMedia&&window.matchMedia('(max-width:759px)').matches&&!isLandscapeTabletViewport());}
  let kggPhoneScrollTimer=0;
  let kggPhoneTouchStart=null;
  let kggPhoneLastMoveAt=0;
  let kggPhonePlanGestureSuppressScrollUntil=0;
  function clearPhoneScrollStateForPlanGesture(ms){
    if(!isPhoneLayout())return;
    const hold=Number.isFinite(ms)?ms:320;
    kggPhonePlanGestureSuppressScrollUntil=Math.max(kggPhonePlanGestureSuppressScrollUntil,Date.now()+hold);
    kggPhoneLastMoveAt=0;
    clearTimeout(kggPhoneScrollTimer);
    document.body.classList.remove('is-scrolling');
  }
  function isPhonePlanCardGestureActive(){
    return isPhoneLayout()&&(
      document.body.classList.contains('kggPlanCardSwiping')||
      document.body.classList.contains('kggPlanCardReordering')
    );
  }
  function markPhoneUserScrolling(){
    if(!isPhoneLayout())return;
    if(isPhonePlanCardGestureActive()||Date.now()<kggPhonePlanGestureSuppressScrollUntil){
      clearTimeout(kggPhoneScrollTimer);
      document.body.classList.remove('is-scrolling');
      return;
    }
    kggPhoneLastMoveAt=Date.now();
    document.body.classList.add('is-scrolling');
    clearTimeout(kggPhoneScrollTimer);
    kggPhoneScrollTimer=setTimeout(()=>document.body.classList.remove('is-scrolling'),220);
  }
  function isPhoneUserScrolling(){
    return isPhoneLayout()&&(document.body.classList.contains('is-scrolling')||(Date.now()-kggPhoneLastMoveAt)<260);
  }
  function trackPhoneTouchStart(ev){
    if(!isPhoneLayout())return;
    const point=ev.touches&&ev.touches[0]||ev;
    kggPhoneTouchStart={x:point.clientX||0,y:point.clientY||0,moved:false};
  }
  function trackPhoneTouchMove(ev){
    if(!isPhoneLayout())return;
    const point=ev.touches&&ev.touches[0]||ev;
    if(kggPhoneTouchStart){
      const dx=Math.abs((point.clientX||0)-kggPhoneTouchStart.x);
      const dy=Math.abs((point.clientY||0)-kggPhoneTouchStart.y);
      if(dx>6||dy>6)kggPhoneTouchStart.moved=true;
    }
    markPhoneUserScrolling();
  }
  function trackPhoneTouchEnd(){
    if(kggPhoneTouchStart&&kggPhoneTouchStart.moved)markPhoneUserScrolling();
    kggPhoneTouchStart=null;
  }
  function shouldIgnorePhoneScrollToggle(){
    return isPhoneUserScrolling();
  }
  function guardPhoneScrollToggle(ev){
    if(!shouldIgnorePhoneScrollToggle())return false;
    if(ev){
      ev.preventDefault();
      ev.stopPropagation();
    }
    return true;
  }
  function initPhoneScrollGuard(){
    if(window.__kggPhoneScrollGuardBound)return;
    window.__kggPhoneScrollGuardBound=true;
    window.addEventListener('scroll',markPhoneUserScrolling,{passive:true});
    document.addEventListener('touchstart',trackPhoneTouchStart,{passive:true});
    document.addEventListener('touchmove',trackPhoneTouchMove,{passive:true});
    document.addEventListener('touchend',trackPhoneTouchEnd,{passive:true});
    document.addEventListener('touchcancel',trackPhoneTouchEnd,{passive:true});
    document.addEventListener('pointermove',ev=>{if(ev.pointerType==='touch')markPhoneUserScrolling();},{passive:true});
  }
  let phoneInputKeepVisibleTimer=0;
  function updatePhoneKeyboardInset(){
    if(!isPhoneLayout()){
      document.body.classList.remove('phoneTextFocus');
      document.documentElement.style.removeProperty('--kgg-phone-keyboard-inset');
      return;
    }
    const vv=window.visualViewport||null;
    const inset=vv?Math.max(0,window.innerHeight-vv.height-vv.offsetTop):0;
    document.documentElement.style.setProperty('--kgg-phone-keyboard-inset',Math.round(inset)+'px');
  }
  function keepPhoneTextInputVisible(){
    const input=$('exerciseInput'), wrap=$('inputWrap');
    if(!isPhoneLayout()||!input||!wrap){
      updatePhoneKeyboardInset();
      return;
    }
    updatePhoneKeyboardInset();
    if(document.activeElement!==input)return;
    if(isPhoneUserScrolling())return;
    document.body.classList.add('phoneTextFocus');
    clearTimeout(phoneInputKeepVisibleTimer);
  }
  function releasePhoneTextFocusSoon(){
    setTimeout(()=>{
      if(document.activeElement!==$('exerciseInput'))document.body.classList.remove('phoneTextFocus');
    },140);
  }
  function markPhoneButtonFloat(id){
    if(!isPhoneLayout()||isPhoneUserScrolling())return;
    const btn=$(id);
    if(!btn)return;
    btn.classList.remove('phoneButtonFloat');
    void btn.offsetWidth;
    btn.classList.add('phoneButtonFloat');
    setTimeout(()=>{
      if(document.body.classList.contains('kggPhoneDrawerOpen')&&(id==='recentToggle'||id==='packageToggle'))return;
      btn.classList.remove('phoneButtonFloat');
    },430);
  }
  function initPhoneKeyboardAndDrawers(){
    initPhoneScrollGuard();
    const input=$('exerciseInput');
    if(input){
      input.addEventListener('focus',keepPhoneTextInputVisible);
      input.addEventListener('input',keepPhoneTextInputVisible);
      input.addEventListener('blur',releasePhoneTextFocusSoon);
    }
    ['bankToggle','recentToggle','packageToggle'].forEach(id=>{
      const btn=$(id);
      if(btn)btn.addEventListener('pointerup',()=>markPhoneButtonFloat(id),{passive:true});
    });
    window.addEventListener('resize',()=>{if(isPhoneUserScrolling()){updatePhoneKeyboardInset();return;} keepPhoneTextInputVisible();});
    window.addEventListener('orientationchange',()=>setTimeout(keepPhoneTextInputVisible,180));
    if(window.visualViewport){
      window.visualViewport.addEventListener('resize',()=>{if(isPhoneUserScrolling()){updatePhoneKeyboardInset();return;} keepPhoneTextInputVisible();});
      window.visualViewport.addEventListener('scroll',()=>{markPhoneUserScrolling(); updatePhoneKeyboardInset();});
    }
  }
  function renderDbTitle(dbTitle,text){
    if(!dbTitle)return;
    const isOpen=!!state.bankOpen;
    const mode=isOpen?(text?'open-search':'open-full'):'closed';
    dbTitle.classList.toggle('hidden',!isOpen);
    dbTitle.classList.toggle('fullBankOpen',isOpen&&!text);
    dbTitle.classList.toggle('searchBankOpen',isOpen&&!!text);
    if(dbTitle.dataset.titleMode!==mode){
      dbTitle.innerHTML=isOpen?'<span class="dbTitleTrain">\u00dcbungsdatenbank</span>':'&#9656; &#x1f3cb;&#xfe0f; \u00dcbungsdatenbank';
      dbTitle.dataset.titleMode=mode;
    }
    dbTitle.setAttribute('aria-expanded',isOpen?'true':'false');
    dbTitle.setAttribute('aria-label',isOpen?'\u00dcbungsdatenbank schlie\u00dfen':'\u00dcbungsdatenbank \u00f6ffnen');
  }
  function render(){const rawText=activeText(); const text=activeBankQuerySegment(); const hasPlan=state.plan.length>0; const dbTitle=$('dbTitle'), inputLabel=$('inputLabel'); $('stateBadge').textContent=state.bankOpen?(text?'DB offen mit Text':'DB offen ohne Text'):(rawText?'Textfeld aktiv':(hasPlan?'Aktueller Plan':'Leerzustand')); $('createPanel').classList.toggle('planMode',hasPlan); $('planActions').classList.toggle('hasPlan',hasPlan); $('panelTitle').textContent=hasPlan?'✏️ Aktueller Plan':'➕ Neuen Plan erstellen'; inputLabel.textContent='Übungen eingeben'; inputLabel.classList.toggle('hidden',state.bankOpen||hasPlan); $('finishBtn').classList.toggle('hidden',!hasPlan); $('savePackageBtn').classList.toggle('hidden',!hasPlan); renderDbTitle(dbTitle,text); renderSuggestion(text); renderBank(text); bindBankSwipeDelete($('bankContent')); renderPlan(); renderRecent(); renderPackages(); $('patientMini').textContent=state.patient.name||''; updateToggleCarets(); setTabletAnchorActiveClasses(); updatePhoneKeyboardInset();}
  function bankLetterForName(name){const first=String(name||'').trim().charAt(0).toUpperCase(); return /^[A-ZÄÖÜ]$/.test(first)?first:'#';}
  function renderSuggestion(text){
    const tabletBank=isTabletLayout();
    bankSelectMode=(state.bankOpen||tabletBank)?(text?'replaceActive':'append'):'replaceActive';
    const el=$('suggestion');
    if(!text || state.bankOpen || tabletBank){el.classList.add('hidden'); el.onclick=null; el.innerHTML=''; return;}
    const hit=search(text,1)[0];
    if(!hit){el.classList.add('hidden'); el.onclick=null; el.innerHTML=''; return;}
    el.innerHTML='<div class="row"><button class="iconBtn" type="button" data-open-top8 aria-label="Top-8-Treffer öffnen">▸ 🏋️</button><button class="iconBtn" type="button" data-apply-hit aria-label="Treffer übernehmen"><b>'+escapeHtml(hit.name)+'</b></button></div>';
    el.classList.remove('hidden');
    el.onclick=null;
    const open=el.querySelector('[data-open-top8]');
    const apply=el.querySelector('[data-apply-hit]');
    if(open)open.onclick=ev=>{ev.preventDefault();ev.stopPropagation();state.bankOpen=true;render();};
    if(apply){preventButtonFocusSteal(apply); apply.onclick=ev=>{ev.preventDefault();ev.stopPropagation();applySelectedExerciseToText(hit,{keepFocus:true});};}
  }
  function nextAvailableBankLetter(requested,available){const letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split(''); const wanted=String(requested||'').toUpperCase(); const start=Math.max(0,letters.indexOf(wanted)); for(let i=start;i<letters.length;i++){if(available.includes(letters[i]))return letters[i];} for(let i=start-1;i>=0;i--){if(available.includes(letters[i]))return letters[i];} return available[0]||'';}
  function setActiveAzLetter(nav,letter){if(!nav)return; nav.querySelectorAll('[data-jump]').forEach(btn=>btn.classList.toggle('active',btn.dataset.jump===letter));}
  function setAzTouchPreview(nav,letter){
    if(!nav)return;
    const buttons=[...nav.querySelectorAll('[data-jump]')];
    const index=buttons.findIndex(btn=>btn.dataset.jump===letter);
    buttons.forEach((btn,i)=>{
      const dist=index<0?99:Math.abs(i-index);
      btn.classList.toggle('touch-preview',dist===0);
      btn.classList.toggle('touch-near1',dist===1);
      btn.classList.toggle('touch-near2',dist===2);
    });
  }
  function jumpBankToLetter(container,letter,instant){const nav=container&&container.querySelector('.az'); const rowsWrap=container&&container.querySelector('.bankRows'); if(!container||!rowsWrap)return; const available=[...container.querySelectorAll('.bankRow[data-letter]')].map(row=>row.dataset.letter).filter((l,i,a)=>l&&a.indexOf(l)===i); const targetLetter=nextAvailableBankLetter(letter,available); if(!targetLetter)return; const target=container.querySelector('.bankRow[data-letter="'+targetLetter+'"]'); if(target){const rowRect=target.getBoundingClientRect(); const wrapRect=rowsWrap.getBoundingClientRect(); const nextTop=Math.max(0,rowsWrap.scrollTop+(rowRect.top-wrapRect.top)); rowsWrap.scrollTo({top:nextTop,behavior:instant?'auto':'smooth'}); setActiveAzLetter(nav,targetLetter);}}
  function azLetterFromPoint(nav,clientY){if(!nav)return''; const rect=nav.getBoundingClientRect(); const buttons=[...nav.querySelectorAll('[data-jump]')]; if(!buttons.length)return''; const ratio=Math.max(0,Math.min(1,(clientY-rect.top)/Math.max(1,rect.height))); return buttons[Math.min(buttons.length-1,Math.floor(ratio*buttons.length))].dataset.jump;}
  function bindAzScrollrad(container){const nav=container&&container.querySelector('.az'); if(!nav||nav.dataset.azBound==='1')return; nav.dataset.azBound='1'; let active=false,tapTimer=0; const setTouching=on=>{nav.classList.toggle('azTouching',!!on); if(!on)setAzTouchPreview(nav,'');}; const showTapWave=letter=>{clearTimeout(tapTimer); nav.classList.add('azTouching'); setAzTouchPreview(nav,letter); tapTimer=setTimeout(()=>setTouching(false),180);}; const jumpFromEvent=ev=>{const touch=ev.touches&&ev.touches[0]||ev.changedTouches&&ev.changedTouches[0]; const y=touch?touch.clientY:ev.clientY; const letter=azLetterFromPoint(nav,y); if(letter){setAzTouchPreview(nav,letter); jumpBankToLetter(container,letter,true);}}; nav.addEventListener('click',ev=>{const btn=ev.target&&ev.target.closest?ev.target.closest('[data-jump]'):null; if(!btn||!nav.contains(btn))return; ev.preventDefault(); showTapWave(btn.dataset.jump); jumpBankToLetter(container,btn.dataset.jump);}); nav.addEventListener('pointerdown',ev=>{clearTimeout(tapTimer); active=true; setTouching(true); nav.setPointerCapture&&nav.setPointerCapture(ev.pointerId); ev.preventDefault(); jumpFromEvent(ev);}); nav.addEventListener('pointermove',ev=>{if(!active)return; ev.preventDefault(); jumpFromEvent(ev);}); nav.addEventListener('pointerup',ev=>{active=false; setTouching(false); try{nav.releasePointerCapture&&nav.releasePointerCapture(ev.pointerId);}catch(e){}}); nav.addEventListener('pointercancel',()=>{active=false; setTouching(false);}); nav.addEventListener('touchstart',ev=>{clearTimeout(tapTimer); active=true; setTouching(true); jumpFromEvent(ev);},{passive:false}); nav.addEventListener('touchmove',ev=>{if(!active)return; ev.preventDefault(); jumpFromEvent(ev);},{passive:false}); nav.addEventListener('touchend',()=>{active=false; setTouching(false);},{passive:true});}
  function bankCardThumbnailHtml(ex){
    const media=ensureExerciseMediaList(ex).find(item=>item&&item.type==='image'&&item.id);
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
```
