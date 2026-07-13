# KGG Source Chunk 049

- Source: `kgg-update/index.html`
- Lines: 20581-21000

```html
      if(!record||!record.blob)throw new Error('Lokale Bilddatei fehlt.');
      const imageBlob=await patientDecryptMedia(media,record.blob);
      const url=URL.createObjectURL(imageBlob);
      preview.innerHTML='<img src="'+url+'" alt="Uebungsbild Vorschau">';
      setTimeout(()=>URL.revokeObjectURL(url),60000);
    }catch(err){
      preview.textContent='Vorschau lokal nicht verfuegbar.';
    }
  }
  function renderEditorMediaStatus(ex){
    const box=document.querySelector('.editorMediaBox'), status=$('editMediaStatus'), removeBtn=$('removeExerciseImage');
    if(!box||!status||!removeBtn)return;
    const isEditableExercise=!!ex;
    box.classList.toggle('hidden',!isEditableExercise);
    if(!isEditableExercise){clearEditorMediaPreview();return;}
    const media=ensureExerciseMediaList(ex);
    removeBtn.classList.toggle('hidden',media.length===0);
    if(!media.length){status.textContent='Kein Bild.';clearEditorMediaPreview();return;}
    const first=media[0];
    status.textContent='1 Bild · '+mediaSizeLabel(first.encryptedSize||first.compressedSize||first.originalSize);
    renderEditorMediaPreview(first);
  }
  async function handleEditorMediaFileSelected(ev){
    const file=ev.target.files&&ev.target.files[0];
    ev.target.value='';
    if(!file)return;
    const ex=currentEditedExercise();
    if(!ex)return;
    const status=$('editMediaStatus');
    if(status)status.textContent='Bild wird vorbereitet ...';
    const oldMedia=ensureExerciseMediaList(ex);
    try{
      const manifest=await prepareImageMediaFile(file);
      ex.media=[manifest];
      oldMedia.forEach(item=>deleteUnsharedMediaBlob(item,ex));
      if(ex.localId){
        syncStatePlanToStore('ui_attach_exercise_image');
        save();
      }else{
        ex.custom=true;
        ex.updatedAt=new Date().toISOString();
        persistCustomBank();
      }
      renderEditorMediaStatus(ex);
      render();
      $('editorModal').classList.add('open');
    }catch(err){
      console.warn('Bild konnte nicht vorbereitet werden:',err);
      if(status)status.textContent='Bild fehlgeschlagen.';
    }
  }
  function removeEditorMedia(){
    const ex=currentEditedExercise();
    if(!ex)return;
    const oldMedia=ensureExerciseMediaList(ex);
    ex.media=[];
    oldMedia.forEach(item=>deleteUnsharedMediaBlob(item,ex));
    if(ex.localId){
      syncStatePlanToStore('ui_remove_exercise_image');
      save();
    }else{
      ex.custom=true;
      ex.updatedAt=new Date().toISOString();
      persistCustomBank();
    }
    renderEditorMediaStatus(ex);
    render();
    $('editorModal').classList.add('open');
  }
  function openEditor(ex){
    if(!ex)return;
    const inferredMeasure=(String(ex.unit||ex.metricUnit||'').toLowerCase().includes('zeit')||String(ex.unit||ex.metricUnit||'').toLowerCase().includes('sek'))?'zeit':'wdh';
    state.editId=ex.localId||ex.id;
    $('editName').value=ex.name||'';
    $('editSets').value=String(normalizeSetCount(ex.sets));
    $('editMetric').value=ex.startMetric||'';
    $('editLoad').value=ex.startLoad||'';
    $('editUnit').value=normalizeLoadUnit(ex.weightUnit||ex.loadUnit||'kg');
    $('editMeasure').value=normalizeMeasureMode(ex.measure||inferredMeasure);
    $('editSide').value=normalizeSideMode(ex.side||'BI');
    $('editVideoUrl').value=ex.videoUrl||'';
    $('editVideoLabel').value=ex.videoLabel||'Video öffnen';
    renderEditorMediaStatus(ex);
    const bankEdit=!ex.localId&&bank.some(item=>String(item.id)===String(ex.id));
    $('deleteExercise').dataset.scope=bankEdit?'bank':'plan';
    $('deleteExercise').style.visibility=(ex.localId||bankEdit)?'visible':'hidden';
    $('editorModal').classList.add('open');
  }
  function closeEditor(){state.editId=null; $('editorModal').classList.remove('open')}
  function saveEditedExercise(){
    const id=state.editId;
    const planEx=state.plan.find(x=>(x.localId||x.id)===id);
    if(planEx){
      const measure=normalizeMeasureMode($('editMeasure').value);
      const loadUnit=normalizeLoadUnit($('editUnit').value);
      planEx.name=$('editName').value;
      planEx.sets=normalizeSetCount($('editSets').value);
      planEx.startMetric=$('editMetric').value;
      planEx.startLoad=$('editLoad').value;
      planEx.weightUnit=loadUnit;
      planEx.loadUnit=loadUnit;
      planEx.measure=measure;
      planEx.unit=measureUnitLabel(measure);
      planEx.metricUnit=measureUnitLabel(measure);
      planEx.side=normalizeSideMode($('editSide').value);
      planEx.videoUrl=String($('editVideoUrl').value||'').trim();
      planEx.videoLabel=String($('editVideoLabel').value||'').trim()||'Video öffnen';
      planEx.changedByLiveText=false;
      planEx.needsReview=false;
      const bankEx=upsertPlanExerciseToBank(planEx,'ui_save_exercise');
      if(bankEx){
        planEx.sourceId=bankEx.id;
        planEx.bankId=bankEx.id;
      }
      persistCustomBank();
      syncStatePlanToStore('ui_save_exercise');
      syncTextInputFromPlan('ui_save_exercise');
      save();
      render();
    }else{
      const bankEx=currentEditedBankExercise();
      if(bankEx){
        const measure=normalizeMeasureMode($('editMeasure').value);
        const loadUnit=normalizeLoadUnit($('editUnit').value);
        bankEx.name=$('editName').value;
        bankEx.aliases=bankEx.aliases||bankEx.name;
        bankEx.sets=normalizeSetCount($('editSets').value);
        bankEx.startMetric=$('editMetric').value;
        bankEx.startLoad=$('editLoad').value;
        bankEx.weightUnit=loadUnit;
        bankEx.loadUnit=loadUnit;
        bankEx.measure=measure;
        bankEx.unit=measureUnitLabel(measure);
        bankEx.metricUnit=measureUnitLabel(measure);
        bankEx.side=normalizeSideMode($('editSide').value);
        bankEx.videoUrl=String($('editVideoUrl').value||'').trim();
        bankEx.videoLabel=String($('editVideoLabel').value||'').trim()||'Video öffnen';
        bankEx.custom=true;
        bankEx.updatedAt=new Date().toISOString();
        persistCustomBank();
        render();
      }
    }
    closeEditor();
  }
  function escapeHtml(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
  function exportData(){savePendingToBank('ui_internal_export'); const plan=getCurrentPlanForOutput('ui_internal_export'); const data={kind:'kgg-html-app-internal-export',audience:'therapist-internal-only',version:VERSION,exportedAt:new Date().toISOString(),state:{...state,plan:plan.exercises},currentPlan:plan,store:ensureKGGDataStore().getState()}; const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='kgg_plan_internal_export.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);}

  function chunkArray(items,size){const pages=[]; for(let i=0;i<items.length;i+=size)pages.push(items.slice(i,i+size)); return pages.length?pages:[[]];}
  function safePdfString(value,fallback){return String(value==null||value===''?(fallback||''):value).replace(/[|\n\r]+/g,' ').replace(/\s+/g,' ').trim();}
  function buildPainScale(){return Array.from({length:10},(_,i)=>({value:i+1,label:String(i+1),marked:false}));}
  function buildPdfDayRows(ex){
    const rows=[];
    const sets=Math.max(0,Math.min(3,Number(ex&&ex.sets||3)||3));
    for(let i=1;i<=3;i++){
      rows.push({
        setNo:i,
        setLabel:'S'+i,
        active:i<=sets,
        columns:{
          kg:{label:'kg',unit:ex&&ex.loadUnit||'kg',value:'',suggested:ex&&ex.startLoad||''},
          wdh:{label:'Wdh',unit:ex&&ex.metricUnit||'Wdh',value:'',suggested:ex&&ex.startMetric||''},
          pain:{label:'Schmerz 1-10',value:'',scale:buildPainScale()}
        }
      });
    }
    return rows;
  }
  function buildPdfTables(ex){
    return Array.from({length:6},(_,i)=>({
      tableNo:i+1,
      tableLabel:'T'+(i+1),
      meaning:'Trainingstag '+(i+1),
      rows:buildPdfDayRows(ex)
    }));
  }
  function buildEmptyPdfSlot(pageIndex,slotIndex){
    const slotNo=slotIndex+1;
    const exNo='EX'+slotNo;
    const empty={
      sourceId:'',
      globalIndex:null,
      pageIndex:pageIndex+1,
      pageNo:pageIndex+1,
      slotIndex:slotNo,
      slotNo,
      exNo,
      displayLabel:exNo,
      empty:true,
      isEmpty:true,
      name:'',
      side:'',
      sets:0,
      startLoad:'',
      loadUnit:'kg',
      startMetric:'',
      metricUnit:'Wdh',
      machineLine:'#EX|'+slotNo+'|EMPTY|0||kg|Wdh',
      tables:[],
      columns:['kg','Wdh','Schmerz 1-10']
    };
    empty.tables=buildPdfTables(empty);
    return empty;
  }
  function normalizePdfExercise(ex,index,pageIndex,slotIndex){
    const source=ex||{};
    const sets=Math.max(1,Math.min(3,Number(source.sets||3)||3));
    const loadUnit=safePdfString(source.weightUnit||source.loadUnit,'kg')||'kg';
    const metricUnit=safePdfString(source.unit||source.metricUnit,'Wdh')||'Wdh';
    const slotNo=slotIndex+1;
    const exNo='EX'+slotNo;
    const name=safePdfString(source.name,'Übung '+(index+1));
    const side=safePdfString(source.side||source.sides||source.laterality,'');
    const normalized={
      sourceId:safePdfString(source.localId||source.id||''),
      globalIndex:index+1,
      pageIndex:pageIndex+1,
      pageNo:pageIndex+1,
      slotIndex:slotNo,
      slotNo,
      exNo,
      displayLabel:exNo+' · '+name,
      empty:false,
      isEmpty:false,
      name,
      side,
      sets,
      startLoad:safePdfString(source.startLoad||source.load||source.weight||''),
      loadUnit,
      startMetric:safePdfString(source.startMetric||source.metric||source.reps||''),
      metricUnit,
      rawText:safePdfString(source.rawText||''),
      source:safePdfString(source.source||source.sourceId||source.bankId||''),
      flags:Array.isArray(source.sourceFlags)?source.sourceFlags.slice():[],
      machineLine:'#EX|'+slotNo+'|'+name+'|'+sets+'|'+side+'|'+loadUnit+'|'+metricUnit,
      columns:['kg','Wdh','Schmerz 1-10'],
      tables:[]
    };
    normalized.tables=buildPdfTables(normalized);
    return normalized;
  }
  function buildKggPdfSnapshot(plan,options){
    const sourcePlan=plan||{};
    const exercises=Array.isArray(sourcePlan.exercises)?sourcePlan.exercises:[];
    const patient=sourcePlan.patient||{};
    const opts=options||{};
    const largeSingleRow=opts.layout==='large-single-row';
    const slotsPerPage=largeSingleRow?3:6;
    const gridCols=largeSingleRow?1:2;
    const gridRows=3;
    const exerciseLabels=Array.from({length:slotsPerPage},(_,i)=>'EX'+(i+1));
    const pages=chunkArray(exercises,slotsPerPage).map((items,pageIndex)=>{
      const slots=[];
      for(let slotIndex=0;slotIndex<slotsPerPage;slotIndex++){
        const ex=items[slotIndex];
        slots.push(ex?normalizePdfExercise(ex,(pageIndex*slotsPerPage)+slotIndex,pageIndex,slotIndex):buildEmptyPdfSlot(pageIndex,slotIndex));
      }
      return {
        pageNo:pageIndex+1,
        pageIndex:pageIndex+1,
        pageCount:null,
        exRange:'EX1-EX'+slotsPerPage,
        layoutSlots:slotsPerPage,
        slotCount:slotsPerPage,
        slots,
        exercises:slots,
        emptySlotCount:slots.filter(s=>s.empty).length
      };
    });
    pages.forEach(p=>p.pageCount=pages.length);
    const snapshot={
      kind:'kgg-pdf-snapshot',
      version:2,
      createdAt:new Date().toISOString(),
      source:'KGGDataStore.currentPlan via getCurrentPlanForOutput(ui_make_pdf)',
      planId:safePdfString(sourcePlan.id||''),
      planTitle:safePdfString(sourcePlan.title||'KGG Plan','KGG Plan'),
      updatedAt:safePdfString(sourcePlan.updatedAt||''),
      patient:{
        name:safePdfString(patient.name||''),
        id:safePdfString(patient.id||patient.patientId||''),
        initials:safePdfString(patient.initials||''),
        startDate:safePdfString(patient.date||patient.startDate||sourcePlan.startDate||''),
        therapist:safePdfString(patient.therapist||patient.therapistName||''),
        notes:safePdfString(patient.notes||patient.info||sourcePlan.notes||''),
        reason:safePdfString(patient.reason||sourcePlan.reason||'KGG','KGG')||'KGG',
        displayName:safePdfString(patient.name||patient.initials||patient.id||'Patient/in','Patient/in')
      },
      layoutTarget:{
        templateId:largeSingleRow?'TPL-BASIS-A-GROSSDRUCK-L3-v3':'TPL-BASIS-A-CLASSIC-L6-v2',
        paper:largeSingleRow?'A4 gross portrait':'A4',
        orientation:largeSingleRow?'portrait':'landscape',
        grid:gridCols+'x'+gridRows,
        exercisesPerPage:slotsPerPage,
        cornerMarkers:'black',
        exerciseLabels,
        machineLineFormat:'#EX|slot|name|sets|side|loadUnit|metricUnit',
        tables:['T1','T2','T3','T4','T5','T6'],
        sets:['S1','S2','S3'],
        columns:['kg','Wdh','Schmerz 1-10'],
        renderedInThisPatch:false
      },
      tableContract:{
        days:['T1','T2','T3','T4','T5','T6'],
        setRows:['S1','S2','S3'],
        columns:[
          {key:'kg',label:'kg',type:'number',patientWritable:true},
          {key:'wdh',label:'Wdh',type:'numberOrTime',patientWritable:true},
          {key:'pain',label:'Schmerz 1-10',type:'scale',min:1,max:10,patientWritable:true}
        ]
      },
      pages,
      exerciseCount:exercises.length,
      pageCount:pages.length,
      emptySlotCount:pages.reduce((sum,p)=>sum+p.emptySlotCount,0),
      audience:'pdf-output-not-json-patient-file',
      jsonPolicy:'JSON bleibt intern; Patient:innen bekommen PDF oder Patienten-App/QR, keine JSON-Datei.',
      pdfRuntimeFingerprint:PDF_RUNTIME_FINGERPRINT
    };
    window.KGGLatestPdfSnapshot=snapshot;
    return snapshot;
  }
  function firstPdfExerciseImageMedia(ex){
    return ensureExerciseMediaList(ex).find(item=>item&&item.type==='image'&&item.id) || null;
  }
  async function createKggPdfThumbnailDataUrl(imageBlob){
    const img=await loadImageFromBlob(imageBlob);
    const targetW=150,targetH=110;
    const canvas=document.createElement('canvas');
    canvas.width=targetW; canvas.height=targetH;
    const ctx=canvas.getContext('2d',{alpha:false});
    ctx.fillStyle='#fff'; ctx.fillRect(0,0,targetW,targetH);
    const iw=img.naturalWidth||img.width||1,ih=img.naturalHeight||img.height||1;
    const scale=Math.min(targetW/iw,targetH/ih);
    const dw=Math.max(1,Math.round(iw*scale));
    const dh=Math.max(1,Math.round(ih*scale));
    const dx=Math.round((targetW-dw)/2),dy=Math.round((targetH-dh)/2);
    ctx.imageSmoothingEnabled=true;
    ctx.imageSmoothingQuality='high';
    try{ctx.filter='grayscale(1) contrast(1.08)';}catch(e){}
    ctx.drawImage(img,dx,dy,dw,dh);
    try{
      const data=ctx.getImageData(0,0,targetW,targetH);
      for(let i=0;i<data.data.length;i+=4){
        const grey=Math.round((data.data[i]*0.299)+(data.data[i+1]*0.587)+(data.data[i+2]*0.114));
        data.data[i]=grey; data.data[i+1]=grey; data.data[i+2]=grey; data.data[i+3]=255;
      }
      ctx.putImageData(data,0,0);
    }catch(e){}
    return canvas.toDataURL('image/jpeg',.68);
  }
  async function loadKggPdfExerciseThumbnail(sourceExercise){
    const media=firstPdfExerciseImageMedia(sourceExercise);
    if(!media)return null;
    try{
      const record=await getEncryptedMediaBlob(media.id);
      if(!record||!record.blob)return null;
      const imageBlob=await patientDecryptMedia(media,record.blob);
      const dataUrl=await createKggPdfThumbnailDataUrl(imageBlob);
      if(!/^data:image\/jpeg;base64,/i.test(dataUrl))return null;
      return {
        kind:'kgg-pdf-exercise-thumbnail',
        sourceId:String(media.id||''),
        mime:'image/jpeg',
        width:150,
        height:110,
        dataUrl
      };
    }catch(err){
      console.warn('PDF-Uebungsbild wird ausgelassen:',err);
      return null;
    }
  }
  async function attachKggPdfExerciseThumbnails(snapshot,plan){
    const sourceExercises=Array.isArray(plan&&plan.exercises)?plan.exercises:[];
    if(!snapshot||!sourceExercises.length)return snapshot;
    let count=0;
    const slots=(snapshot.pages||[]).flatMap(page=>page.slots||page.exercises||[]);
    await Promise.all(slots.map(async slot=>{
      if(!slot||slot.empty)return;
      const source=sourceExercises[Math.max(0,Number(slot.globalIndex||0)-1)];
      if(!source)return;
      const thumb=await loadKggPdfExerciseThumbnail(source);
      if(!thumb)return;
      slot.pdfThumbnail=thumb;
      slot.hasPdfThumbnail=true;
      count++;
    }));
    snapshot.thumbnailCount=count;
    snapshot.thumbnailMode='local-indexeddb-grayscale';
    return snapshot;
  }
  function findJsPdfConstructor(){return (window.jspdf&&window.jspdf.jsPDF)||window.jsPDF||null;}
  function ensureJsPdfForPdfTest(){
    const existing=findJsPdfConstructor();
    if(existing)return Promise.resolve(existing);
    if(typeof window.KGGLoadJsPdfForTest==='function')return window.KGGLoadJsPdfForTest().then(()=>findJsPdfConstructor());
    return Promise.resolve(null);
  }
  function getPdfPageSize(doc){
    const ps=doc&&doc.internal&&doc.internal.pageSize||{};
    const w=typeof ps.getWidth==='function'?ps.getWidth():ps.width||297;
    const h=typeof ps.getHeight==='function'?ps.getHeight():ps.height||210;
    return {w,h};
  }
  function pdfSetFont(doc,size,style){
    try{doc.setFont('helvetica',style||'normal');}catch(e){}
    doc.setFontSize(size);
  }
  function pdfText(doc,text,x,y,opts){
    doc.text(String(text==null?'':text),x,y,opts||{});
  }
  function pdfShort(text,max){
    const s=String(text==null?'':text).replace(/\s+/g,' ').trim();
    return s.length>max?s.slice(0,Math.max(0,max-1))+'…':s;
  }
  function pdfSplitTwoLines(text,firstMax,secondMax){
    const raw=String(text==null?'':text).replace(/\s+/g,' ').trim();
    if(raw.length<=firstMax)return [raw];
    const limit=Math.max(1,Number(firstMax)||1);
```
