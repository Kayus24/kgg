# KGG Source Chunk 043

- Source: `kgg-update/index.html`
- Lines: 18061-18480

```html
    if(window.KGGAndroidApkUpdateUrl){
      const target=window.KGGAndroidApkUpdateUrl;
      window.KGGAndroidApkUpdateUrl='';
      closeInstallPrompt();
      try{const opened=window.open(target,'_blank','noopener'); if(!opened)location.href=target;}catch(err){location.href=target;}
      return;
    }
    if(window.KGGRemoteUpdateUrl){
      const target=window.KGGRemoteUpdateUrl;
      window.KGGRemoteUpdateUrl='';
      closeInstallPrompt();
      try{const opened=window.open(target,'_blank','noopener'); if(!opened)location.href=target;}catch(err){location.href=target;}
      return;
    }
    localStorage.setItem(pwaInstallPromptSeenKey,new Date().toISOString());
    const waiting=window.KGGWaitingServiceWorker;
    if(waiting){waiting.postMessage({type:'SKIP_WAITING'}); closeInstallPrompt(); return;}
    if(deferredInstallPrompt){
      const prompt=deferredInstallPrompt;
      deferredInstallPrompt=null;
      try{prompt.prompt(); await prompt.userChoice;}catch(err){console.warn('Install-Prompt blockiert:',err);}
    }
    closeInstallPrompt();
  }
  function initPwaAndUpdates(){
    initStoragePersistence();
    setTimeout(checkGithubAppUpdate,900);
    setInterval(checkGithubAppUpdate,kggAutoUpdateCheckMs);
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')checkGithubAppUpdate();});
    window.addEventListener('beforeinstallprompt',ev=>{
      ev.preventDefault();
      deferredInstallPrompt=ev;
      showInstallPrompt('install');
    });
    window.addEventListener('appinstalled',()=>localStorage.setItem(pwaInstallPromptSeenKey,new Date().toISOString()));
    if(!canUsePwaRuntime()||isLocalHtmlTestRuntime()||!('serviceWorker' in navigator))return;
    navigator.serviceWorker.register(pwaServiceWorkerUrl).then(reg=>{
      reg.update().catch(()=>{});
      reg.addEventListener('updatefound',()=>{
        const worker=reg.installing;
        if(!worker)return;
        worker.addEventListener('statechange',()=>{
          if(worker.state==='installed'&&navigator.serviceWorker.controller){
            window.KGGWaitingServiceWorker=worker;
            worker.postMessage({type:'SKIP_WAITING'});
          }
        });
      });
    }).catch(err=>console.warn('Service Worker konnte nicht registriert werden:',err));
    navigator.serviceWorker.addEventListener('controllerchange',()=>{if(!window.KGGPwaReloading){window.KGGPwaReloading=true; location.reload();}});
  }
  function initAdminModeAccess(){
    loadAdminSecrets();
    exposeAdminSecretApi();
    document.body.classList.add('adminMode');
    if(!(adminSecrets.geminiKeys&&adminSecrets.geminiKeys.length)){
      setTimeout(()=>{try{openAdminSecretsModal();}catch(e){}},700);
    }
  }
  function applyLargePdfMode(){
    const enabled=!!state.largePdfMode;
    const btn=$('visionBtn');
    if(btn){btn.textContent=enabled?'PDF A-':'PDF A+'; btn.setAttribute('aria-pressed',enabled?'true':'false'); btn.title=enabled?'Standard-PDF':'Großdruck-PDF';}
  }
  function setLargePdfMode(enabled){state.largePdfMode=!!enabled; applyLargePdfMode(); save();}
  function initLargePdfMode(){if(/[?&](grosspdf|largepdf)=1\b/i.test(location.search))state.largePdfMode=true; applyLargePdfMode();}
  function loadDeletedBankIds(){try{const raw=localStorage.getItem(deletedBankKey); const ids=raw?JSON.parse(raw):[]; deletedBankIds=new Set(Array.isArray(ids)?ids.map(String):[]);}catch(e){console.warn(e); deletedBankIds=new Set();}}
  function persistDeletedBankIds(){try{localStorage.setItem(deletedBankKey,JSON.stringify([...deletedBankIds]));}catch(e){console.warn(e)}}
  function loadCustomBank(){loadDeletedBankIds(); try{const raw=localStorage.getItem(customBankKey); const items=raw?JSON.parse(raw):[]; if(Array.isArray(items))items.forEach(ex=>{if(ex&&ex.name){const existing=bank.find(b=>compact(b.name)===compact(ex.name)); if(existing)Object.assign(existing,{...ex,id:existing.id||ex.id,custom:true}); else bank.push({...ex,custom:true});}});}catch(e){console.warn(e)} for(let i=bank.length-1;i>=0;i--){if(deletedBankIds.has(String(bank[i]&&bank[i].id)))bank.splice(i,1);}}
  function persistCustomBank(){try{localStorage.setItem(customBankKey,JSON.stringify(bank.filter(ex=>ex.custom||ex.createdFromPlan)));}catch(e){console.warn(e)} queueNativeExerciseBankSync('exercise_bank_changed');}
  function openBankDeleteModal(id){
    const ex=bank.find(item=>String(item.id)===String(id));
    if(!ex)return;
    pendingBankDeleteId=String(id);
    const name=$('bankDeleteName');
    if(name)name.textContent=ex.name||'';
    $('bankDeleteModal').classList.add('open');
  }
  function closeBankDeleteModal(){pendingBankDeleteId=null; $('bankDeleteModal').classList.remove('open');}
  function deleteBankExercise(id){
    const sid=String(id||'');
    const idx=bank.findIndex(ex=>String(ex&&ex.id)===sid);
    if(idx<0)return;
    deletedBankIds.add(sid);
    bank.splice(idx,1);
    persistDeletedBankIds();
    persistCustomBank();
    render();
  }
  function confirmBankDelete(){if(pendingBankDeleteId)deleteBankExercise(pendingBankDeleteId); closeBankDeleteModal();}
  function exerciseBankFieldsFromPlan(ex,name){
    return {
      name:name||ex.name||stripExerciseName(ex.rawText)||'',
      aliases:ex.aliases||name||ex.name||'',
      sets:normalizeSetCount(ex.sets),
      unit:ex.unit||ex.metricUnit||'Wdh',
      weightUnit:ex.weightUnit||ex.loadUnit||'kg',
      loadUnit:ex.weightUnit||ex.loadUnit||'kg',
      metricUnit:ex.unit||ex.metricUnit||'Wdh',
      measure:normalizeMeasureMode(ex.measure||(String(ex.unit||'').toLowerCase().includes('zeit')?'zeit':'wdh')),
      side:normalizeSideMode(ex.side||'BI'),
      startMetric:ex.startMetric||'',
      startLoad:ex.startLoad||'',
      videoUrl:ex.videoUrl||'',
      videoLabel:ex.videoLabel||'Video öffnen',
      media:ensureExerciseMediaList(ex)
    };
  }
  function upsertPlanExerciseToBank(ex,reason){
    const name=ex&&ex.name||stripExerciseName(ex&&ex.rawText)||'';
    if(!name)return null;
    let existing=bank.find(b=>compact(b.name)===compact(name));
    const fields=exerciseBankFieldsFromPlan(ex,name);
    if(existing){
      Object.assign(existing,fields,{custom:true,updatedFromPlan:true,updatedAt:new Date().toISOString(),dbSyncReason:reason||'plan_save'});
    }else{
      existing={id:'custom_'+Date.now()+'_'+Math.random().toString(36).slice(2,6),...fields,custom:true,createdFromPlan:true,createdAt:new Date().toISOString(),dbSyncReason:reason||'plan_save'};
      bank.push(existing);
    }
    return existing;
  }
  function savePendingToBank(reason){
    state.plan=(state.plan||[]).map(ex=>{
      const copy={...ex};
      if(copy.pendingNew||copy.changedByLiveText||copy.needsReview){
        const saved=upsertPlanExerciseToBank(copy,reason||'before_output');
        if(saved){
          copy.pendingNew=false;
          copy.dbSynced=true;
          copy.dbSyncedAt=new Date().toISOString();
          copy.dbSyncReason=reason||'before_output';
          copy.sourceId=saved.id;
          copy.bankId=saved.id;
        }
      }
      return copy;
    });
    persistCustomBank();
    syncStatePlanToStore(reason||'save_pending_to_bank');
    save();
  }
  function score(q,ex){const cq=compact(q), cn=compact(ex.name), al=String(ex.aliases||'').split(/[,;]/).map(compact); if(!cq)return 0; if(cq===cn)return 120; if(al.indexOf(cq)>-1)return 115; if(cn.includes(cq)||cq.includes(cn))return 94; if(al.some(a=>a.length>2&&(a.includes(cq)||cq.includes(a))))return 90; return norm(q).split(' ').reduce((r,t)=>r+(t.length>2&&norm(ex.name+' '+ex.aliases).includes(t)?10:0),0)}
  function scoredSearch(q,limit){return bank.map(ex=>({ex,score:score(q,ex)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,limit||8)}
  function search(q,limit){return scoredSearch(q,limit).map(x=>x.ex)}
  function allAlpha(){return bank.slice().sort((a,b)=>a.name.localeCompare(b.name,'de'))}
  function fillBankListWithFallback(matches,limit){
    const selected=Array.isArray(matches)?matches.slice(0,limit):[];
    const used=new Set(selected.map(ex=>ex&&ex.id).filter(Boolean));
    for(const ex of allAlpha()){
      if(selected.length>=limit)break;
      if(!used.has(ex.id)){selected.push(ex); used.add(ex.id);}
    }
    return selected;
  }
  function stripExerciseName(raw){return String(raw||'').replace(/\d+(?:[,.]\d+)?\s*(kg|kilo|wdh|wh|reps|min|sek|sec|s)/ig,' ').replace(/(a|x|mal)/ig,' ').replace(/\s+/g,' ').trim();}
  function parseLiveExercise(text,localId){
    const raw=String(text||'').trim();
    const parsedSide=parseSideModeFromText(raw);
    const letters=raw.replace(/[^A-Za-zÄÖÜäöüß]/g,'');
    if(letters.length<3)return null;
    const match=scoredSearch(raw,1)[0]||null;
    const hit=(match&&match.score>=20)?match.ex:null;
    {
      const parsed=parseExerciseQuantityText(raw);
      const cleanName=stripExerciseName(raw)||raw;
      const pendingNew=!hit || (match&&match.score<35);
      const needsReview=pendingNew || parsed.needsReview || (!!match && match.score>0 && match.score<70);
      const id=localId||makeLocalId();
      const base=hit||{id:'new_'+Date.now(),name:cleanName,sets:3,unit:parsed.unit||'Wdh',weightUnit:parsed.weightUnit||'kg',loadUnit:parsed.loadUnit||parsed.weightUnit||'kg'};
      const loadUnit=parsed.weightUnit||parsed.loadUnit||base.weightUnit||base.loadUnit||'kg';
      return {...base, id, localId:id, sourceId:hit?hit.id:'', bankId:hit?hit.id:'', name:hit?hit.name:cleanName, sets:(hit&&hit.sets)||3, unit:parsed.unit||base.unit||'Wdh', metricUnit:parsed.metricUnit||parsed.unit||base.metricUnit||base.unit||'Wdh', weightUnit:loadUnit, loadUnit, explicitLoadUnit:!!(parsed.weightUnit||parsed.loadUnit), startMetric:parsed.startMetric, startLoad:parsed.startLoad, side:parsedSide, rawText:raw, liveDraft:true, changedByLiveText:true, pendingNew, needsReview, customLoadUnit:parsed.customLoadUnit||undefined, sourceFlags:[pendingNew?'pendingNew':'',needsReview?'needsReview':'',parsed.customLoadUnit?'customUnit':''].filter(Boolean)};
    }
    const nums=raw.match(/\d+(?:[,.]\d+)?/g)||[];
    let metric='',load='';
    const kg=raw.match(/(\d+(?:[,.]\d+)?)\s*kg/i);
    const rep=raw.match(/(\d+)\s*(wdh|wh|reps)/i);
    const time=raw.match(/(\d+(?:[,.]\d+)?)\s*(min|sek|sec|s)/i);
    if(rep) metric=rep[1]; else if(time) metric=time[1].replace(',','.')+' '+time[2].toLowerCase();
    if(kg) load=kg[1].replace(',','.'); else if(nums.length>1 && !time) load=nums[0].replace(',','.');
    const cleanName=stripExerciseName(raw)||raw;
    const pendingNew=!hit || (match&&match.score<35);
    const needsReview=pendingNew || (!!match && match.score>0 && match.score<70);
    const id=localId||makeLocalId();
    return {...(hit||{id:'new_'+Date.now(),name:cleanName,sets:3,unit:(time?'Zeit':'Wdh'),weightUnit:(kg?'kg':'kg')}), id, localId:id, sourceId:hit?hit.id:'', bankId:hit?hit.id:'', name:hit?hit.name:cleanName, sets:(hit&&hit.sets)||3, startMetric:metric, startLoad:load, side:parsedSide, rawText:raw, liveDraft:true, changedByLiveText:true, pendingNew, needsReview, sourceFlags:[pendingNew?'pendingNew':'',needsReview?'needsReview':''].filter(Boolean)};
  }
  function parseLine(text){return parseLiveExercise(text)||{id:makeLocalId(),localId:makeLocalId(),name:String(text||'').trim(),sets:3,unit:'Wdh',weightUnit:'kg',pendingNew:true,needsReview:true};}
  function addExercise(ex){const item=ensureUiExerciseShape(ex||{}); state.plan.push(item); syncStatePlanToStore('ui_add_exercise'); $('exerciseInput').value=''; state.bankOpen=false; state.liveDraftId=null; save(); render();}
  function removeExercise(localId){state.plan=state.plan.filter(x=>(x.localId||x.id)!==localId); if(state.liveDraftId===localId)state.liveDraftId=null; if(state.sortMenuId===localId)state.sortMenuId=null; syncStatePlanToStore('ui_remove_exercise'); save(); render();}
  function finalizeLiveDraft(reason){if(!state.liveDraftId)return; const ex=state.plan.find(x=>(x.localId||x.id)===state.liveDraftId); if(ex){ex.liveDraft=false; ex.finalizedFromText=true; ex.finalizedAt=new Date().toISOString();} state.liveDraftId=null; syncStatePlanToStore(reason||'ui_finalize_live_draft'); save();}
  function upsertLiveExerciseFromText(){const text=activeText(); if(!text){finalizeLiveDraft('ui_live_input_empty'); render(); return;} const draft=parseLiveExercise(text,state.liveDraftId||makeLocalId()); if(!draft)return; state.liveDraftId=draft.localId; const idx=state.plan.findIndex(x=>(x.localId||x.id)===draft.localId); if(idx>=0)state.plan[idx]={...state.plan[idx],...draft}; else state.plan.push(draft); syncStatePlanToStore('ui_live_textfield_draft'); save(); render();}
  function isClearableLiveTextExercise(ex,rawText){
    const id=ex&&(ex.localId||ex.id);
    const raw=String(rawText||'').trim();
    const exRaw=String(ex&&ex.rawText||'').trim();
    if(state.liveDraftId && id===state.liveDraftId)return true;
    if(ex&&ex.liveDraft===true)return true;
    if(raw && exRaw && exRaw===raw && (ex.finalizedFromText===true || ex.changedByLiveText===true))return true;
    return false;
  }
  function clearInputAndRemoveLiveTextExercises(){
    const raw=activeText();
    state.plan=(state.plan||[]).filter(ex=>!isClearableLiveTextExercise(ex,raw));
    state.liveDraftId=null;
    $('exerciseInput').value='';
    state.bankOpen=false;
    syncStatePlanToStore('ui_clear_text_remove_live_exercises');
    save();
    render();
  }
  function confirmExerciseInput(){const text=activeText(); if(!text)return; if(state.liveDraftId){finalizeLiveDraft('ui_enter_optional_finalize'); $('exerciseInput').value=''; state.bankOpen=false; render(); return;} addExercise(parseLine(text));}
  function activeText(){return $('exerciseInput').value.trim()}
  function stripExerciseName(raw){
    const n=structuredNumberPattern(), u=structuredUnitPattern();
    let text=String(raw||'');
    text=text.replace(/\s*-\s*Tag\s*\d+\b/ig,' ');
    text=text.replace(/\bTag\s*\d+\b/ig,' ');
    text=text.replace(/\bSchmerz\s*[:=]\s*\d+\s*\/\s*10\b/ig,' ');
    text=text.replace(/\b(?:Satz\s*\d+|S\s*\d+)\s*[:.)_\-]?\s*/ig,' ');
    text=text.replace(/\b\d+\.\s*Satz\s*[:.)_\-]?\s*/ig,' ');
    text=text.replace(/\b\d+\)\s*/g,' ');
    text=text.replace(new RegExp('@\\s*(?:'+n+'\\s*'+u+'?|'+u+'\\s*'+n+'|'+u+')','ig'),' ');
    text=text.replace(new RegExp('\\b'+n+'\\s*x\\s*'+n+'\\s*'+u+'?\\b','ig'),' ');
    text=text.replace(new RegExp('\\b'+n+'\\s*(?:kg|kilo|wdh|wh|rep|reps|min|minute|minutes|minuten|sek\\.?|sec|secs|s|zeit|time|dauer|'+u+')\\b','ig'),' ');
    text=text.replace(new RegExp('\\b(?:'+u+')\\s*'+n+'\\b','ig'),' ');
    return text.replace(/\b(li\/re|l\/r|lr|li|re|links|rechts)\b/ig,' ').replace(/\b(a|x|mal)\b/ig,' ').replace(/\s+/g,' ').trim();
  }
  function splitPlanText(text){
    const value=String(text||'').replace(/\r/g,'');
    const parts=[];
    const re=/\n+|;|,(?=\s*(?:[A-Za-zÄÖÜäöüß]|$))/g;
    let start=0,match;
    while((match=re.exec(value))){
      parts.push({text:value.slice(start,match.index),start:start,end:match.index,separator:value.slice(match.index,re.lastIndex)});
      start=re.lastIndex;
    }
    parts.push({text:value.slice(start),start:start,end:value.length,separator:''});
    return parts;
  }
  function stripStructuredSetPrefix(line){
    return String(line||'').trim()
      .replace(/^\s*Satz\s*\d+\s*[:.)_\-]?\s*/i,'')
      .replace(/^\s*S\s*\d+\s*[:.)_\-]?\s*/i,'')
      .replace(/^\s*\d+\.\s*Satz\s*[:.)_\-]?\s*/i,'')
      .replace(/^\s*\d+\)\s*/i,'')
      .replace(/^\s*\d+\.\s*/i,'');
  }
  function isStructuredSetLine(text){
    const raw=String(text||'').trim();
    if(!/^\s*(?:Satz\s*\d+|S\s*\d+|\d+\.\s*Satz|\d+\))/i.test(raw))return false;
    const body=stripStructuredSetPrefix(raw);
    return /-?\d+(?:[,.]\d+)?/.test(body);
  }
  function isStructuredPainLine(text){
    return /^\s*(?:Schmerz|Pain)\s*[:=]\s*\d+\s*\/\s*10\b/i.test(String(text||'').trim());
  }
  function splitInlineStructuredParts(line){
    const raw=String(line||'').replace(/\s+/g,' ').trim();
    if(!raw)return [];
    const markerRe=/(?:Satz\s*\d+|S\s*\d+|\d+\.\s*Satz|\d+\)|Schmerz)\s*[:.)_\-]?/ig;
    const markers=[];
    let match;
    while((match=markerRe.exec(raw)))markers.push({index:match.index});
    if(!markers.length)return [raw];
    const parts=[];
    if(markers[0].index>0){
      const prefix=raw.slice(0,markers[0].index).trim();
      if(prefix)parts.push(prefix);
    }
    for(let i=0;i<markers.length;i++){
      const start=markers[i].index;
      const end=i+1<markers.length?markers[i+1].index:raw.length;
      const chunk=raw.slice(start,end).trim();
      if(chunk)parts.push(chunk);
    }
    return parts;
  }
  function normalizeStructuredNumber(value){return String(value||'').replace(',','.').trim();}
  function normalizeStructuredLoadUnit(value){
    return normalizeLoadUnit(value||'kg');
  }
  function parseStructuredSetLine(line){
    return parseExerciseQuantityText(stripStructuredSetPrefix(line));
  }
  function structuredPlanBlocksFromText(text){
    const lines=String(text||'').replace(/\r/g,'').split(/\n+/).flatMap(splitInlineStructuredParts).map(line=>line.trim()).filter(Boolean);
    let sawSetLine=false,current=null;
    const blocks=[];
    lines.forEach(line=>{
      if(isStructuredSetLine(line)){
        sawSetLine=true;
        if(current)current.setLines.push(line);
        return;
      }
      if(isStructuredPainLine(line))return;
      if(current)blocks.push(current);
      current={name:line.replace(/\s+/g,' ').trim(),setLines:[]};
    });
    if(current)blocks.push(current);
    if(!sawSetLine)return null;
    return blocks.filter(block=>{
      const letters=String(block.name||'').replace(/[^A-Za-zÄÖÜäöüß]/g,'');
      return letters.length>=3;
    });
  }
  function parseStructuredTextExerciseBlock(block,existing){
    if(!block||!block.name)return null;
    const ex=parseTextExercise(block.name,existing);
    if(!ex)return null;
    const firstInfo=(block.setLines||[]).map(parseStructuredSetLine).find(info=>info.startMetric||info.startLoad)||{};
    const next={...ex,rawText:[block.name].concat(block.setLines||[]).join('\n'),textMaster:true,liveDraft:false,changedByLiveText:false};
    if(firstInfo.startMetric){next.startMetric=firstInfo.startMetric;next.unit=firstInfo.unit||next.unit||'Wdh';next.metricUnit=firstInfo.metricUnit||next.unit||'Wdh';}
    if(firstInfo.startLoad)next.startLoad=firstInfo.startLoad;
    if(firstInfo.weightUnit||firstInfo.loadUnit){next.weightUnit=firstInfo.weightUnit||firstInfo.loadUnit;next.loadUnit=firstInfo.loadUnit||firstInfo.weightUnit;next.explicitLoadUnit=true;}
    if(firstInfo.customLoadUnit){next.customLoadUnit=true;next.needsReview=true;next.sourceFlags=Array.from(new Set([...(next.sourceFlags||[]),'customUnit','needsReview']));}
    return next;
  }
  function structuredExercisesFromPlanText(text){
    const blocks=structuredPlanBlocksFromText(text);
    if(blocks===null)return null;
    return blocks.map((block,index)=>parseStructuredTextExerciseBlock(block,findExistingForTextSegment(block.name,index))).filter(Boolean);
  }
  function activeTextSegment(){
    const input=$('exerciseInput');
    if(!input)return'';
    const parts=splitPlanText(input.value);
    const pos=typeof input.selectionStart==='number'?input.selectionStart:input.value.length;
    const hit=parts.find(p=>pos>=p.start&&pos<=p.end)||parts[parts.length-1];
    return (hit&&hit.text||'').trim();
  }
  function exactBankExercise(name){const c=compact(name); return bank.find(ex=>compact(ex.name)===c)||null;}
  function parseTextExercise(text,existing){
    {
      const raw=String(text||'').trim();
      const letters=raw.replace(/[^A-Za-zÄÖÜäöüß]/g,'');
      if(letters.length<3)return null;
      const parsed=parseExerciseQuantityText(raw);
      const parsedSide=parseSideModeFromText(raw);
      const cleanName=stripExerciseName(raw)||raw;
      const exact=exactBankExercise(cleanName);
      const id=existing&&(existing.localId||existing.id)||makeLocalId();
      const base=exact||existing||{id:'new_'+Date.now(),name:cleanName,sets:3,unit:parsed.unit||'Wdh',weightUnit:parsed.weightUnit||'kg',loadUnit:parsed.loadUnit||parsed.weightUnit||'kg'};
      const pendingNew=!exact;
      const loadUnit=parsed.weightUnit||parsed.loadUnit||base.weightUnit||base.loadUnit||'kg';
      const needsReview=pendingNew||parsed.needsReview;
      return {...base,id,localId:id,sourceId:exact?exact.id:'',bankId:exact?exact.id:'',name:exact?exact.name:cleanName,sets:(existing&&existing.sets)||base.sets||3,unit:parsed.unit||base.unit||'Wdh',metricUnit:parsed.metricUnit||parsed.unit||base.metricUnit||base.unit||'Wdh',weightUnit:loadUnit,loadUnit,explicitLoadUnit:!!(parsed.weightUnit||parsed.loadUnit),startMetric:parsed.startMetric||(existing&&existing.startMetric)||'',startLoad:parsed.startLoad||(existing&&existing.startLoad)||'',side:parsedSide||normalizeSideMode(existing&&existing.side||'BI'),rawText:raw,liveDraft:false,changedByLiveText:false,textMaster:true,pendingNew,needsReview,customLoadUnit:parsed.customLoadUnit||undefined,sourceFlags:[pendingNew?'textMasterReview':'',needsReview?'needsReview':'',parsed.customLoadUnit?'customUnit':''].filter(Boolean)};
    }
    const raw=String(text||'').trim();
    const letters=raw.replace(/[^A-Za-zÄÖÜäöüß]/g,'');
    if(letters.length<3)return null;
    const parsedSide=parseSideModeFromText(raw);
    const nums=raw.match(/\d+(?:[,.]\d+)?/g)||[];
    let metric='',load='';
    const kg=raw.match(/(\d+(?:[,.]\d+)?)\s*kg/i);
    const rep=raw.match(/(\d+)\s*(wdh|wh|reps)/i);
    const time=raw.match(/(\d+(?:[,.]\d+)?)\s*(min|sek|sec|s)\b/i);
    if(rep) metric=rep[1]; else if(time) metric=time[1].replace(',','.')+' '+time[2].toLowerCase();
    if(kg) load=kg[1].replace(',','.'); else if(nums.length>1&&!time) load=nums[0].replace(',','.');
    const cleanName=stripExerciseName(raw)||raw;
    const exact=exactBankExercise(cleanName);
    const id=existing&&(existing.localId||existing.id)||makeLocalId();
    const base=exact||existing||{id:'new_'+Date.now(),name:cleanName,sets:3,unit:(time?'Zeit':'Wdh'),weightUnit:(kg?'kg':'kg')};
    const pendingNew=!exact;
    return {...base,id,localId:id,sourceId:exact?exact.id:'',bankId:exact?exact.id:'',name:exact?exact.name:cleanName,sets:(existing&&existing.sets)||base.sets||3,startMetric:metric||(existing&&existing.startMetric)||'',startLoad:load||(existing&&existing.startLoad)||'',side:parsedSide||normalizeSideMode(existing&&existing.side||'BI'),rawText:raw,liveDraft:false,changedByLiveText:false,textMaster:true,pendingNew,needsReview:pendingNew,sourceFlags:[pendingNew?'textMasterReview':''].filter(Boolean)};
  }
  function findExistingForTextSegment(segment,index){
    const current=(state.plan||[])[index];
    if(current)return current;
    const c=compact(stripExerciseName(segment)||segment);
    return (state.plan||[]).find(ex=>compact(ex.rawText||ex.name)===c)||null;
  }
  function formatExerciseTextLine(ex){
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
```
