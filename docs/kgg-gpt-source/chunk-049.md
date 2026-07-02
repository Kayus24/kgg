# KGG Source Chunk 049

- Source: `kgg-update/index.html`
- Lines: 20581-21000

```html
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
        templateId:largeSingleRow?'TPL-BASIS-A-GROSSDRUCK-L3-v1':'TPL-BASIS-A-CLASSIC-L6-v2',
        paper:largeSingleRow?'A2 gross portrait, A4-Layout 2x skaliert':'A4',
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
    const target=snapshot.layoutTarget||{};
    if(target.grid==='1x3'){
      snapshot.thumbnailCount=0;
      snapshot.thumbnailMode='large-print-skipped';
      return snapshot;
    }
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
  function pdfSpaceLabel(fullLabel,shortLabel,cellWidth,minWidth){
    return Number(cellWidth||0)>=Number(minWidth||0)?fullLabel:shortLabel;
  }
  function pdfResetInk(doc){
    try{doc.setDrawColor(0);doc.setTextColor(0);doc.setFillColor(0);}catch(e){}
  }
  function pdfLightInk(doc){
    try{doc.setDrawColor(155);doc.setTextColor(80);doc.setFillColor(255);}catch(e){}
  }

  function drawKggCornerMarkers(doc,layout){
    const edge=2.6,len=9.4,th=1.9,w=layout.pageW,h=layout.pageH;
    try{doc.setFillColor(0);doc.setDrawColor(0);}catch(e){}
    doc.rect(edge,edge,len,th,'F'); doc.rect(edge,edge,th,len,'F');
    doc.rect(w-edge-len,edge,len,th,'F'); doc.rect(w-edge-th,edge,th,len,'F');
    doc.rect(edge,h-edge-th,len,th,'F'); doc.rect(edge,h-edge-len,th,len,'F');
    doc.rect(w-edge-len,h-edge-th,len,th,'F'); doc.rect(w-edge-th,h-edge-len,th,len,'F');
    pdfResetInk(doc);
  }

  function drawHeaderField(doc,label,value,x,y,w,h){
    pdfResetInk(doc);
    doc.setLineWidth(.16);
    doc.rect(x,y,w,h);
    pdfSetFont(doc,4.7,'bold');
    pdfText(doc,label,x+1.5,y+3.2);
    pdfSetFont(doc,6.2,'normal');
    pdfText(doc,pdfShort(value||'-',34),x+1.5,y+h-2.1);
  }

  function drawKggPdfHeader(doc,snapshot,page,layout){
    const patient=snapshot.patient||{};
    const template=((snapshot.layoutTarget&&snapshot.layoutTarget.templateId)||'TPL-BASIS-A-CLASSIC-L6-v2');
    const pageNo=page&&page.pageNo||1;
    const pageCount=snapshot.pageCount||page&&page.pageCount||1;
    const x=layout.margin,y=layout.margin,w=layout.pageW-(layout.margin*2),h=layout.headerH;
    pdfResetInk(doc);
    doc.setLineWidth(.32);
    try{doc.roundedRect(x,y,w,h,1.5,1.5);}catch(e){doc.rect(x,y,w,h);}
    pdfSetFont(doc,10.4,'bold');
    pdfText(doc,'KGG Trainingsplan',x+3,y+5.7);
    pdfSetFont(doc,5.2,'normal');
    const line1='Patient/in: '+pdfShort(patient.displayName||patient.name||patient.initials||patient.id||'Patient/in',46)+'   Start: '+pdfShort(patient.startDate||'-',20)+'   Anlass: '+pdfShort(patient.reason||'KGG',18);
    pdfText(doc,line1,x+3,y+10.0);
    pdfText(doc,'T1-T6 = Trainingstage   S1-S3 = Sätze',x+3,y+14.1);
    pdfSetFont(doc,4.6,'normal');
    pdfText(doc,template+' · Seite '+pageNo+'/'+pageCount,x+w-3,y+5.6,{align:'right'});
    pdfSetFont(doc,3.8,'normal');
    pdfText(doc,PDF_RUNTIME_FINGERPRINT,x+w-3,y+13.9,{align:'right'});
    pdfResetInk(doc);
  }


  function drawKggTableScaffold(doc,ex,x,y,w,h){
    const side=normalizeSideMode(ex&&ex.side||'BI');
    const loadUnit=String(ex&&ex.loadUnit||'kg')||'kg';
    const metricUnit=String(ex&&ex.metricUnit||'Wdh')||'Wdh';
    const isLR=side==='LR';
    const tagW=10.8;
    const painW=22.5;
    const headH=Math.max(8.6,Math.min(10.2,h*.18));
    const rowH=(h-headH)/6;
    const setW=w-tagW-painW;
    const groupW=setW/3;
    pdfResetInk(doc);
    doc.setLineWidth(.18);
    doc.rect(x,y,w,h);
    doc.rect(x,y,tagW,headH);
    pdfSetFont(doc,4.7,'bold');
    pdfText(doc,'Tag',x+tagW/2,y+headH*.62,{align:'center'});
    for(let s=0;s<3;s++){
      const gx=x+tagW+s*groupW;
      doc.rect(gx,y,groupW,headH);
      pdfSetFont(doc,4.8,'bold');
      pdfText(doc,pdfSpaceLabel('Satz '+(s+1),'S'+(s+1),groupW,isLR?18:16),gx+groupW/2,y+3.1,{align:'center'});
      const subCount=isLR?4:2;
      const subW=groupW/subCount;
      for(let c=1;c<subCount;c++)doc.line(gx+c*subW,y+4.2,gx+c*subW,y+headH);
      pdfSetFont(doc,3.55,'bold');
      const labels=isLR?['li '+loadUnit,'li '+metricUnit,'re '+loadUnit,'re '+metricUnit]:[loadUnit,metricUnit];
      labels.forEach((label,idx)=>pdfText(doc,pdfShort(label,9),gx+subW*(idx+.5),y+headH-1.7,{align:'center'}));
    }
    const painX=x+tagW+setW;
    doc.rect(painX,y,painW,headH);
    pdfSetFont(doc,4.2,'bold');
    pdfText(doc,'Schmerz',painX+painW/2,y+3.2,{align:'center'});
    pdfSetFont(doc,3.4,'bold');
    pdfText(doc,'1-10',painX+painW/2,y+headH-1.7,{align:'center'});
    for(let t=0;t<6;t++){
      const ry=y+headH+t*rowH;
      doc.rect(x,ry,tagW,rowH);
      pdfSetFont(doc,4.8,'bold');
      pdfText(doc,pdfSpaceLabel('Tag '+(t+1),'T'+(t+1),tagW,13),x+tagW/2,ry+rowH*.62,{align:'center'});
      for(let s=0;s<3;s++){
        const gx=x+tagW+s*groupW;
        doc.rect(gx,ry,groupW,rowH);
        const subCount=isLR?4:2;
        const subW=groupW/subCount;
        for(let c=1;c<subCount;c++)doc.line(gx+c*subW,ry,gx+c*subW,ry+rowH);
      }
      doc.rect(painX,ry,painW,rowH);
      const pad=.9,gap=.32;
      const boxW=(painW-pad*2-gap*9)/10;
      const boxH=Math.min(rowH-1.2,boxW*1.05);
      const by=ry+(rowH-boxH)/2;
      for(let n=0;n<10;n++)doc.rect(painX+pad+n*(boxW+gap),by,boxW,boxH);
    }
    pdfResetInk(doc);
  }


  function drawKggExerciseBox(doc,slot,x,y,w,h){
    const ex=slot||{};
    pdfResetInk(doc);
    if(ex.empty){
      try{doc.setDrawColor(115);}catch(e){}
      doc.setLineWidth(.14);
      try{doc.roundedRect(x,y,w,h,1.4,1.4);}catch(e){doc.rect(x,y,w,h);}
      pdfResetInk(doc);
      return;
    }
    doc.setLineWidth(.28);
    try{doc.roundedRect(x,y,w,h,1.6,1.6);}catch(e){doc.rect(x,y,w,h);}
    const labelW=7.4,labelH=6.8;
    const thumb=ex.pdfThumbnail&&ex.pdfThumbnail.dataUrl?ex.pdfThumbnail:null;
    const canDrawThumb=!!(thumb&&typeof doc.addImage==='function');
    const thumbW=canDrawThumb?Math.min(23.5,Math.max(18,w*.18)):0;
    const thumbH=canDrawThumb?Math.min(17.2,Math.max(12,h*.20)):0;
    const thumbX=x+w-thumbW-2.2;
    const thumbY=y+2.1;
    const textMax=canDrawThumb?46:62;
    try{doc.setFillColor(0);}catch(e){}
    doc.rect(x,y,labelW,labelH,'F');
    try{doc.setTextColor(255);}catch(e){}
    pdfSetFont(doc,5.9,'bold');
    pdfText(doc,String(ex.slotNo||ex.slotIndex||''),x+labelW/2,y+4.9,{align:'center'});
    try{doc.setTextColor(0);}catch(e){}
    if(canDrawThumb){
      try{
        doc.setLineWidth(.12);
        try{doc.setDrawColor(185);}catch(e){}
```
