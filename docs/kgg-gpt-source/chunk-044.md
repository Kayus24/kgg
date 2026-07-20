# KGG Source Chunk 044

- Source: `kgg-update/src` modular source
- Lines: 18481-18900

```html
    const parts=[String(ex&&ex.name||'').trim()].filter(Boolean);
    if(normalizeSideMode(ex&&ex.side)==='LR')parts.push('li/re');
    const loadUnit=ex&&(ex.weightUnit||ex.loadUnit);
    if(ex&&ex.startLoad)parts.push(String(ex.startLoad)+' '+(loadUnit||'kg'));
    else if(ex&&(ex.explicitLoadUnit||ex.customLoadUnit)&&loadUnit)parts.push('@ '+loadUnit);
    if(ex&&ex.startMetric)parts.push(String(ex.startMetric)+' '+(ex.unit||ex.metricUnit||'Wdh'));
    return parts.join(' ').trim();
  }
  function withTrailingExerciseComma(text){
    const next=String(text||'').replace(/\s+$/,'');
    return next.trim()?next.replace(/,+$/,'')+', ':'';
  }
  function resizeExerciseInputToContent(){
    const input=$('exerciseInput');
    if(!input)return;
    const hasText=!!input.value.trim();
    input.classList.toggle('hasText',hasText);
    input.style.height='auto';
    input.style.height=hasText?Math.ceil(input.scrollHeight)+'px':'';
    const title=$('dbTitle'), wrap=$('inputWrap');
    if(title&&wrap)title.style.setProperty('--db-title-start-y',Math.ceil(wrap.offsetHeight+12)+'px');
  }
  function syncTextInputFromPlan(reason){
    const input=$('exerciseInput');
    if(!input)return;
    const next=withTrailingExerciseComma((state.plan||[]).map(formatExerciseTextLine).filter(Boolean).join(', '));
    if(input.value!==next){state.textSyncing=true; input.value=next; state.textSyncing=false;}
    state.planText=next;
    resizeExerciseInputToContent();
  }
  function restoreTrailingCommaAfterPlanSync(shouldRestore){
    const input=$('exerciseInput');
    if(!shouldRestore||!input||(state.plan||[]).length===0)return;
    const next=withTrailingExerciseComma(input.value);
    if(input.value!==next){state.textSyncing=true; input.value=next; state.textSyncing=false;}
    state.planText=input.value;
    resizeExerciseInputToContent();
  }
  function syncPlanFromTextInput(reason){
    if(state.textSyncing)return;
    const input=$('exerciseInput');
    resizeExerciseInputToContent();
    const text=input&&input.value||'';
    const structured=structuredExercisesFromPlanText(text);
    if(structured!==null)state.plan=structured.map(ensureUiExerciseShape);
    else{
      const segments=splitPlanText(text).map(p=>p.text.trim()).filter(Boolean);
      state.plan=segments.map((segment,index)=>parseTextExercise(segment,findExistingForTextSegment(segment,index))).filter(Boolean).map(ensureUiExerciseShape);
    }
    state.liveDraftId=null;
    state.planText=input?input.value:'';
    syncStatePlanToStore(reason||'ui_textfield_master_sync');
    save();
    render();
  }
  function captureDbScrollAnchor(){
    const anchor=$('bankArea')||$('inputWrap');
    if(!anchor)return null;
    const rows=document.querySelector('#bankContent .bankRows');
    return {top:anchor.getBoundingClientRect().top,rowsTop:rows?rows.scrollTop:0};
  }
  function restoreDbScrollAnchor(anchor){
    if(!anchor||!state.bankOpen)return;
    const rows=document.querySelector('#bankContent .bankRows');
    if(rows)rows.scrollTop=anchor.rowsTop||0;
    const el=$('bankArea')||$('inputWrap');
    if(!el)return;
    const apply=()=>{
      const delta=el.getBoundingClientRect().top-anchor.top;
      if(Math.abs(delta)>1)window.scrollBy(0,delta);
      const nextRows=document.querySelector('#bankContent .bankRows');
      if(nextRows)nextRows.scrollTop=anchor.rowsTop||0;
    };
    apply();
    if(typeof requestAnimationFrame==='function')requestAnimationFrame(apply);
  }
  function alignFullBankInputToViewportTop(){
    const inputWrap=$('inputWrap');
    if(!inputWrap)return;
    const apply=()=>{
      const top=inputWrap.getBoundingClientRect().top;
      const targetOffset=6;
      if(Math.abs(top-targetOffset)>1)window.scrollBy({top:top-targetOffset,behavior:'smooth'});
    };
    if(typeof requestAnimationFrame==='function'){
      requestAnimationFrame(()=>requestAnimationFrame(apply));
    }else{
      setTimeout(apply,0);
    }
  }
  function toggleBankOpenFromUi(){
    const opening=!state.bankOpen;
    const fullBankMode=opening&&!activeBankQuerySegment();
    state.bankOpen=opening;
    render();
    if(fullBankMode)alignFullBankInputToViewportTop();
  }
  function appendExerciseLineToInput(input,line){
    let base=String(input.value||'').replace(/\s+$/,'');
    const prefix=base.trim()?(/[,\n;]$/.test(base)?' ':', '):'';
    input.value=base+prefix+line;
    input.value=withTrailingExerciseComma(input.value);
    return input.value.length;
  }
  function keepExerciseInputFocus(caret){
    const input=$('exerciseInput');
    if(!input||!input.focus)return;
    const apply=()=>{
      try{input.focus({preventScroll:true});}catch(e){input.focus();}
      if(typeof caret==='number'&&input.setSelectionRange)input.setSelectionRange(caret,caret);
    };
    apply();
    if(typeof requestAnimationFrame==='function')requestAnimationFrame(apply);
  }
  function preventButtonFocusSteal(btn){
    if(!btn)return;
    const keep=ev=>ev.preventDefault();
    btn.addEventListener('pointerdown',keep);
    btn.addEventListener('mousedown',keep);
    if(typeof window!=='undefined'&&!window.PointerEvent)btn.addEventListener('touchstart',keep,{passive:false});
  }
  function applySelectedExerciseToText(ex,options){
    if(!ex)return;
    const keepBankOpen=state.bankOpen;
    const bankArea=$('bankArea');
    const defaultMode=bankSelectMode||(state.bankOpen&&bankArea&&bankArea.classList.contains('alphaBankOpen')?'append':'replaceActive');
    const mode=options&&options.mode||defaultMode;
    const keepFocus=!!(options&&options.keepFocus);
    const input=$('exerciseInput');
    const scrollAnchor=state.bankOpen?captureDbScrollAnchor():null;
    const line=formatExerciseTextLine({...ex,side:normalizeSideMode(ex.side||'BI')})||ex.name;
    if(!input){addExercise(ex);return;}
    if(mode==='append'){
      const caret=appendExerciseLineToInput(input,line);
      input.setSelectionRange&&input.setSelectionRange(caret,caret);
      state.bankOpen=keepBankOpen;
      bankSelectMode='append';
      syncPlanFromTextInput('ui_select_db_exercise_append_to_text');
      restoreDbScrollAnchor(scrollAnchor);
      if(keepFocus)keepExerciseInputFocus(caret);
      bankSelectMode='append';
      return;
    }
    const parts=splitPlanText(input.value);
    const pos=typeof input.selectionStart==='number'?input.selectionStart:input.value.length;
    let index=parts.findIndex(p=>pos>=p.start&&pos<=p.end);
    if(index<0)index=Math.max(0,parts.length-1);
    const target=parts[index];
    let caret=pos;
    if(target&&target.text.trim()){
      const parsed=parseTextExercise(target.text,state.plan[index]||null)||{};
      const replacement=formatExerciseTextLine({...ex,localId:parsed.localId||parsed.id,id:parsed.localId||parsed.id,side:parsed.side||ex.side,startLoad:parsed.startLoad,startMetric:parsed.startMetric,weightUnit:ex.weightUnit||parsed.weightUnit,unit:ex.unit||parsed.unit});
      input.value=input.value.slice(0,target.start)+replacement+input.value.slice(target.end);
      caret=target.start+replacement.length;
      const tail=input.value.slice(caret);
      const existingSep=tail.match(/^(\s*(?:,|;|\n+)\s*)/);
      if(existingSep)caret+=existingSep[1].length;
    }else{
      const start=target?target.start:input.value.length;
      const end=target?target.end:input.value.length;
      const before=input.value.slice(0,start);
      const after=input.value.slice(end);
      const needsSeparator=before.trim()&&!/[,\n;]\s*$/.test(before);
      const insert=(needsSeparator?', ':'')+line;
      input.value=before+insert+after;
      caret=before.length+insert.length;
    }
    if(!input.value.slice(caret).trim()){
      const before=input.value.slice(0,caret).replace(/\s+$/,'');
      input.value=withTrailingExerciseComma(before);
      caret=input.value.length;
    }
    input.setSelectionRange&&input.setSelectionRange(caret,caret);
    state.bankOpen=keepBankOpen;
    syncPlanFromTextInput('ui_select_db_exercise_into_text');
    restoreDbScrollAnchor(scrollAnchor);
    if(keepFocus)keepExerciseInputFocus(caret);
    bankSelectMode=keepBankOpen?'append':'replaceActive';
  }
  function addExercise(ex){const item=ensureUiExerciseShape(ex||{}); state.plan.push(item); syncStatePlanToStore('ui_add_exercise'); syncTextInputFromPlan('ui_add_exercise'); state.bankOpen=false; state.liveDraftId=null; save(); render();}
  function removeExercise(localId){const input=$('exerciseInput'); const keepTrailingComma=!!(input&&/,\s*$/.test(input.value)); state.plan=state.plan.filter(x=>(x.localId||x.id)!==localId); if(state.liveDraftId===localId)state.liveDraftId=null; if(state.sortMenuId===localId)state.sortMenuId=null; syncStatePlanToStore('ui_remove_exercise'); syncTextInputFromPlan('ui_remove_exercise'); restoreTrailingCommaAfterPlanSync(keepTrailingComma); save(); render();}
  function clearInputAndRemoveLiveTextExercises(){state.plan=[]; state.liveDraftId=null; $('exerciseInput').value=''; resizeExerciseInputToContent(); state.bankOpen=false; syncStatePlanToStore('ui_clear_text_master_plan'); save(); render();}
  function confirmExerciseInput(){syncPlanFromTextInput('ui_confirm_text_master');}
  function upsertLiveExerciseFromText(){const input=$('exerciseInput'); const value=String(input&&input.value||''); const parts=splitPlanText(value).map(p=>String(p.text||'').trim()).filter(Boolean); const committed=/[,;\\n]\\s*$/.test(value)||parts.length>1; if(!committed){const hadDraft=!!state.liveDraftId||(state.plan||[]).some(ex=>ex&&ex.liveDraft); if(hadDraft){state.plan=(state.plan||[]).filter(ex=>!(ex&&ex.liveDraft)); state.liveDraftId=null; syncStatePlanToStore('ui_textfield_unconfirmed_not_plan'); save();} render(); return;} syncPlanFromTextInput('ui_textfield_master_input');}
  function activeText(){return activeTextSegment();}
  function hasSearchLetters(text){return /[A-Za-zÄÖÜäöüß]/.test(String(text||''));}
  function activeBankQuerySegment(){
    const input=$('exerciseInput');
    if(!input)return'';
    const value=String(input.value||'');
    const pos=typeof input.selectionStart==='number'?input.selectionStart:value.length;
    const before=value.slice(0,pos);
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
```
