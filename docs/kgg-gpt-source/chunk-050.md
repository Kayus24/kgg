# KGG Source Chunk 050

- Source: `kgg-update/src` modular source
- Lines: 21001-21420

```html
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
    let cut=raw.lastIndexOf(' ',limit);
    if(cut<Math.max(12,limit*.55))cut=limit;
    const first=raw.slice(0,cut).trim();
    const rest=raw.slice(cut).trim();
    return [first,pdfShort(rest,secondMax)];
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
    const largePrint=((snapshot.layoutTarget&&snapshot.layoutTarget.grid)==='1x3');
    const pageNo=page&&page.pageNo||1;
    const pageCount=snapshot.pageCount||page&&page.pageCount||1;
    const x=layout.margin,y=layout.margin,w=layout.pageW-(layout.margin*2),h=layout.headerH;
    pdfResetInk(doc);
    doc.setLineWidth(largePrint?0.38:0.32);
    try{doc.roundedRect(x,y,w,h,1.5,1.5);}catch(e){doc.rect(x,y,w,h);}
    pdfSetFont(doc,largePrint?14.2:10.4,'bold');
    pdfText(doc,'KGG Trainingsplan',x+3,y+(largePrint?7.6:5.7));
    pdfSetFont(doc,largePrint?7.4:5.2,'normal');
    const line1='Patient/in: '+pdfShort(patient.displayName||patient.name||patient.initials||patient.id||'Patient/in',largePrint?38:46)+'   Start: '+pdfShort(patient.startDate||'-',18)+'   Anlass: '+pdfShort(patient.reason||'KGG',16);
    pdfText(doc,line1,x+3,y+(largePrint?13.6:10.0));
    pdfText(doc,'T1-T6 = Trainingstage   S1-S3 = Sätze',x+3,y+(largePrint?19.2:14.1));
    pdfSetFont(doc,largePrint?5.9:4.6,'normal');
    pdfText(doc,template+' · Seite '+pageNo+'/'+pageCount,x+w-3,y+(largePrint?7.4:5.6),{align:'right'});
    pdfSetFont(doc,largePrint?4.3:3.8,'normal');
    pdfText(doc,PDF_RUNTIME_FINGERPRINT,x+w-3,y+(largePrint?19.0:13.9),{align:'right'});
    pdfResetInk(doc);
  }


  function drawKggTableScaffold(doc,ex,x,y,w,h,options){
    const largePrint=!!(options&&options.largePrint);
    const side=normalizeSideMode(ex&&ex.side||'BI');
    const loadUnit=String(ex&&ex.loadUnit||'kg')||'kg';
    const metricUnit=String(ex&&ex.metricUnit||'Wdh')||'Wdh';
    const isLR=side==='LR';
    const tagW=largePrint?15.0:10.8;
    const painW=largePrint?32.0:22.5;
    const headH=largePrint?Math.max(14.6,Math.min(16.0,h*.32)):Math.max(8.6,Math.min(10.2,h*.18));
    const rowH=(h-headH)/6;
    const setW=w-tagW-painW;
    const groupW=setW/3;
    pdfResetInk(doc);
    doc.setLineWidth(largePrint?0.28:0.18);
    doc.rect(x,y,w,h);
    doc.rect(x,y,tagW,headH);
    pdfSetFont(doc,largePrint?7.4:4.7,'bold');
    pdfText(doc,'Tag',x+tagW/2,y+headH*.62,{align:'center'});
    for(let s=0;s<3;s++){
      const gx=x+tagW+s*groupW;
      doc.rect(gx,y,groupW,headH);
      pdfSetFont(doc,largePrint?7.5:4.8,'bold');
      pdfText(doc,pdfSpaceLabel('Satz '+(s+1),'S'+(s+1),groupW,isLR?18:16),gx+groupW/2,y+(largePrint?5.5:3.1),{align:'center'});
      const subCount=isLR?4:2;
      const subW=groupW/subCount;
      for(let c=1;c<subCount;c++)doc.line(gx+c*subW,y+(largePrint?7.4:4.2),gx+c*subW,y+headH);
      pdfSetFont(doc,largePrint?7.0:3.55,'bold');
      const labels=isLR?['li '+loadUnit,'li '+metricUnit,'re '+loadUnit,'re '+metricUnit]:[loadUnit,metricUnit];
      labels.forEach((label,idx)=>pdfText(doc,pdfShort(label,9),gx+subW*(idx+.5),y+headH-(largePrint?2.4:1.7),{align:'center'}));
    }
    const painX=x+tagW+setW;
    doc.rect(painX,y,painW,headH);
    pdfSetFont(doc,largePrint?7.2:4.2,'bold');
    pdfText(doc,'Schmerz',painX+painW/2,y+(largePrint?5.3:3.2),{align:'center'});
    pdfSetFont(doc,largePrint?7.0:3.4,'bold');
    pdfText(doc,'1-10',painX+painW/2,y+headH-(largePrint?2.4:1.7),{align:'center'});
    for(let t=0;t<6;t++){
      const ry=y+headH+t*rowH;
      doc.rect(x,ry,tagW,rowH);
      pdfSetFont(doc,largePrint?7.0:4.8,'bold');
      pdfText(doc,pdfSpaceLabel('Tag '+(t+1),'T'+(t+1),tagW,13),x+tagW/2,ry+rowH*.62,{align:'center'});
      for(let s=0;s<3;s++){
        const gx=x+tagW+s*groupW;
        doc.rect(gx,ry,groupW,rowH);
        const subCount=isLR?4:2;
        const subW=groupW/subCount;
        for(let c=1;c<subCount;c++)doc.line(gx+c*subW,ry,gx+c*subW,ry+rowH);
      }
      doc.rect(painX,ry,painW,rowH);
      const pad=largePrint?1.4:0.9,gap=largePrint?0.38:0.32;
      const boxW=(painW-pad*2-gap*9)/10;
      const boxH=Math.min(rowH-(largePrint?1.6:1.2),boxW*1.05);
      const by=ry+(rowH-boxH)/2;
      for(let n=0;n<10;n++)doc.rect(painX+pad+n*(boxW+gap),by,boxW,boxH);
    }
    pdfResetInk(doc);
  }


  function drawKggExerciseBox(doc,slot,x,y,w,h,options){
    const largePrint=!!(options&&options.largePrint);
    const ex=slot||{};
    pdfResetInk(doc);
    if(ex.empty){
      try{doc.setDrawColor(115);}catch(e){}
      doc.setLineWidth(largePrint?0.18:0.14);
      try{doc.roundedRect(x,y,w,h,1.4,1.4);}catch(e){doc.rect(x,y,w,h);}
      pdfResetInk(doc);
      return;
    }
    doc.setLineWidth(largePrint?0.34:0.28);
    try{doc.roundedRect(x,y,w,h,1.6,1.6);}catch(e){doc.rect(x,y,w,h);}
    const labelW=largePrint?11.4:7.4,labelH=largePrint?10.0:6.8;
    const thumb=ex.pdfThumbnail&&ex.pdfThumbnail.dataUrl?ex.pdfThumbnail:null;
    const canDrawThumb=!!(thumb&&typeof doc.addImage==='function');
    const thumbW=canDrawThumb?(largePrint?Math.min(38,Math.max(32,w*.19)):Math.min(23.5,Math.max(18,w*.18))):0;
    const thumbH=canDrawThumb?(largePrint?Math.min(27.5,Math.max(22,h*.30)):Math.min(17.2,Math.max(12,h*.20))):0;
    const thumbX=x+w-thumbW-(largePrint?3.0:2.2);
    const thumbY=y+(largePrint?2.7:2.1);
    const textMax=largePrint?(canDrawThumb?58:82):(canDrawThumb?46:62);
    try{doc.setFillColor(0);}catch(e){}
    doc.rect(x,y,labelW,labelH,'F');
    try{doc.setTextColor(255);}catch(e){}
    pdfSetFont(doc,largePrint?9.0:5.9,'bold');
    pdfText(doc,String(ex.slotNo||ex.slotIndex||''),x+labelW/2,y+(largePrint?7.2:4.9),{align:'center'});
    try{doc.setTextColor(0);}catch(e){}
    if(canDrawThumb){
      try{
        doc.setLineWidth(largePrint?0.16:0.12);
        try{doc.setDrawColor(185);}catch(e){}
        doc.rect(thumbX-.45,thumbY-.45,thumbW+.9,thumbH+.9);
        doc.addImage(thumb.dataUrl,'JPEG',thumbX,thumbY,thumbW,thumbH);
      }catch(err){console.warn('PDF-Thumbnail konnte nicht gezeichnet werden:',err);}
      pdfResetInk(doc);
    }
    pdfSetFont(doc,largePrint?14.0:7.1,'bold');
    const titleText=(ex.exNo||'EX')+' · '+(ex.name||'Übung');
    if(largePrint){
      const titleLines=pdfSplitTwoLines(titleText,textMax,canDrawThumb?52:70);
      pdfText(doc,titleLines[0],x+labelW+3.2,y+8.9);
      if(titleLines[1])pdfText(doc,titleLines[1],x+labelW+3.2,y+15.6);
    }else{
      pdfText(doc,pdfShort(titleText,textMax),x+labelW+2.3,y+5.0);
    }
    const sideLabel=sideModeLabel(ex.side||'BI');
    const startParts=[];
    if(ex.startLoad)startParts.push('Startlast '+ex.startLoad+' '+(ex.loadUnit||'kg'));
    if(ex.startMetric)startParts.push('Startwert '+ex.startMetric+' '+(ex.metricUnit||'Wdh'));
    const meta=[(ex.sets||3)+' Sätze',sideLabel].concat(startParts).concat([(ex.loadUnit||'kg'),(ex.metricUnit==='Wdh'?'Wiederholungen':(ex.metricUnit||'Wdh'))]).join(' · ');
    pdfSetFont(doc,largePrint?8.6:4.55,'normal');
    pdfText(doc,pdfShort(meta,largePrint?(canDrawThumb?92:118):(canDrawThumb?64:95)),x+labelW+(largePrint?3.2:2.3),y+(largePrint?23.2:9.1));
    pdfSetFont(doc,largePrint?6.2:3.35,'normal');
    pdfText(doc,pdfShort(ex.machineLine||'',largePrint?(canDrawThumb?112:146):(canDrawThumb?82:128)),x+labelW+(largePrint?3.2:2.3),y+(largePrint?29.0:12.5));
    const tableY=y+(largePrint?36.0:15.2);
    drawKggTableScaffold(doc,ex,x+(largePrint?2.0:1.6),tableY,w-(largePrint?4.0:3.2),h-(tableY-y)-(largePrint?2.0:1.5),{largePrint});
    pdfResetInk(doc);
  }


  function drawKggPdfLayoutV1(doc,snapshot){
    const size=getPdfPageSize(doc);
    const target=snapshot.layoutTarget||{};
    const largeSingleRow=target.grid==='1x3';
    const layout={pageW:size.w,pageH:size.h,margin:largeSingleRow?6.0:5.4,headerH:largeSingleRow?23.0:17.5,gap:largeSingleRow?2.8:2.6};
    const gridTop=layout.margin+layout.headerH+(largeSingleRow?3.2:3.1);
    const footerH=largeSingleRow?4.6:3.8;
    const gridH=layout.pageH-gridTop-layout.margin-footerH;
    const cols=largeSingleRow?1:2,rows=3;
    const slotLimit=cols*rows;
    const boxW=(layout.pageW-(layout.margin*2)-(layout.gap*(cols-1)))/cols;
    const boxH=(gridH-(layout.gap*(rows-1)))/rows;
    const pages=(snapshot.pages&&snapshot.pages.length?snapshot.pages:[{pageNo:1,pageCount:1,slots:[]}]);
    const pageOrientation=(target.orientation||'landscape');
    pages.forEach((page,pageIdx)=>{
      if(pageIdx>0)doc.addPage('a4',pageOrientation);
      pdfResetInk(doc);
      drawKggCornerMarkers(doc,layout);
      drawKggPdfHeader(doc,snapshot,page,layout);
      const slots=(page.slots||page.exercises||[]).slice(0,slotLimit);
      while(slots.length<slotLimit)slots.push({empty:true});
      slots.forEach((slot,slotIdx)=>{
        const col=slotIdx%cols;
        const row=Math.floor(slotIdx/cols);
        const x=layout.margin+col*(boxW+layout.gap);
        const y=gridTop+row*(boxH+layout.gap);
        drawKggExerciseBox(doc,slot,x,y,boxW,boxH,{largePrint:largeSingleRow});
      });
      pdfResetInk(doc);
      pdfSetFont(doc,largeSingleRow?4.4:3.75,'normal');
      const template=(snapshot.layoutTarget&&snapshot.layoutTarget.templateId)||'TPL-BASIS-A-CLASSIC-L6-v2';
      pdfText(doc,'KGG|'+template+'|'+(page.pageNo||pageIdx+1)+'/'+(snapshot.pageCount||pages.length)+'|#EX-Layout|'+(snapshot.createdAt||'').slice(0,10),layout.pageW-layout.margin,layout.pageH-2.2,{align:'right'});
      pdfSetFont(doc,largeSingleRow?3.9:3.3,'normal');
      pdfText(doc,PDF_RUNTIME_FINGERPRINT,layout.margin,layout.pageH-2.2);
    });
  }

  function createScaledPdfDoc(doc,scale,options){
    const s=Number(scale)||1;
    const opts=options||{};
    const virtualW=Number(opts.virtualW)||297,virtualH=Number(opts.virtualH)||210;
    const pageOrientation=opts.orientation||(virtualW>virtualH?'landscape':'portrait');
    const scaled={
      internal:{pageSize:{width:virtualW,height:virtualH,getWidth:()=>virtualW,getHeight:()=>virtualH}},
      addPage:(_format,orientation)=>{doc.addPage([virtualW*s,virtualH*s],orientation||pageOrientation);return scaled;},
      setFont:(family,style)=>{doc.setFont(family,style);return scaled;},
      setFontSize:size=>{doc.setFontSize(Number(size||0)*s);return scaled;},
      setLineWidth:width=>{doc.setLineWidth(Number(width||0)*s);return scaled;},
      setDrawColor:(...args)=>{doc.setDrawColor(...args);return scaled;},
      setTextColor:(...args)=>{doc.setTextColor(...args);return scaled;},
      setFillColor:(...args)=>{doc.setFillColor(...args);return scaled;},
      rect:(x,y,w,h,style)=>{doc.rect(x*s,y*s,w*s,h*s,style);return scaled;},
      roundedRect:(x,y,w,h,rx,ry,style)=>{try{doc.roundedRect(x*s,y*s,w*s,h*s,(rx||0)*s,(ry||0)*s,style);}catch(e){doc.rect(x*s,y*s,w*s,h*s,style);}return scaled;},
      line:(x1,y1,x2,y2)=>{doc.line(x1*s,y1*s,x2*s,y2*s);return scaled;},
      text:(text,x,y,opts)=>{doc.text(String(text==null?'':text),x*s,y*s,opts||{});return scaled;}
    };
    return scaled;
  }

  function drawKggLargePrintPdfLayout(doc,snapshot){
    const size=getPdfPageSize(doc);
    const layout={pageW:size.w,pageH:size.h,margin:10,gap:7};
    const patient=snapshot.patient||{};
    const exercises=(snapshot.pages||[]).flatMap(page=>(page.slots||page.exercises||[])).filter(ex=>ex&&!ex.empty);
    let pageNo=0,y=0;
    const startPage=()=>{
      if(pageNo>0)doc.addPage('a4','landscape');
      pageNo+=1;
      y=layout.margin;
      pdfResetInk(doc);
      doc.setLineWidth(.45);
      try{doc.roundedRect(layout.margin,y,layout.pageW-layout.margin*2,21,2,2);}catch(e){doc.rect(layout.margin,y,layout.pageW-layout.margin*2,21);}
      pdfSetFont(doc,18,'bold');
      pdfText(doc,'KGG Trainingsplan - Grossdruck',layout.margin+5,y+8.2);
      pdfSetFont(doc,9,'normal');
      const line='Patient/in: '+pdfShort(patient.displayName||patient.name||'Patient/in',42)+'   Start: '+pdfShort(patient.startDate||'-',16);
      pdfText(doc,line,layout.margin+5,y+16.2);
      y+=29;
    };
    const drawCard=(ex,index)=>{
      const cardH=34;
      if(y+cardH>layout.pageH-layout.margin-6)startPage();
      const x=layout.margin,w=layout.pageW-layout.margin*2;
      doc.setLineWidth(.35);
      try{doc.roundedRect(x,y,w,cardH,2,2);}catch(e){doc.rect(x,y,w,cardH);}
      pdfSetFont(doc,15,'bold');
      pdfText(doc,(index+1)+'. '+pdfShort(ex.name||'Uebung',56),x+5,y+8.5);
      const side=sideModeLabel(ex.side||'BI');
      const meta=[];
      meta.push('Saetze: '+(ex.sets||3));
      meta.push('Ausfuehrung: '+side);
      if(ex.startLoad)meta.push('Startlast: '+ex.startLoad+' '+(ex.loadUnit||'kg'));
      if(ex.startMetric)meta.push('Startwert: '+ex.startMetric+' '+(ex.metricUnit||'Wdh'));
      meta.push('Eintragen: kg / Wiederholungen oder Zeit / Schmerz 1-10');
      pdfSetFont(doc,9.6,'normal');
      pdfText(doc,pdfShort(meta.join('  |  '),118),x+5,y+18.3);
      pdfSetFont(doc,8.2,'normal');
      pdfText(doc,'Trainingstage 1 bis 6 - bitte Werte nach jedem Training notieren.',x+5,y+27.2);
      y+=cardH+layout.gap;
    };
    startPage();
    if(!exercises.length){
      pdfSetFont(doc,14,'bold');
      pdfText(doc,'Keine Uebungen im Plan.',layout.margin+5,y+12);
    }else{
      exercises.forEach(drawCard);
    }
    pdfResetInk(doc);
    pdfSetFont(doc,6.5,'normal');
    pdfText(doc,PDF_RUNTIME_FINGERPRINT,layout.margin,layout.pageH-3.2);
  }

  function pdfBytesFromBinaryString(pdf){
    const bytes=new Uint8Array(pdf.length);
    for(let i=0;i<pdf.length;i++)bytes[i]=pdf.charCodeAt(i)&255;
    return bytes;
  }
  function pdfBlobFromDoc(doc){
    if(!doc)return null;
    if(typeof doc.output==='function'){
      try{
        const blob=doc.output('blob');
        if(blob instanceof Blob)return blob;
      }catch(e){}
      try{
        const buffer=doc.output('arraybuffer');
        if(buffer)return new Blob([buffer],{type:'application/pdf'});
      }catch(e){}
      try{
        const text=doc.output();
        if(typeof text==='string')return new Blob([pdfBytesFromBinaryString(text)],{type:'application/pdf'});
      }catch(e){}
    }
    if(typeof doc._buildPdf==='function'){
      try{return new Blob([pdfBytesFromBinaryString(doc._buildPdf())],{type:'application/pdf'});}catch(e){}
    }
    return null;
  }
  function downloadPdfBlob(blob,filename){
    if(!blob)return;
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;
    a.download=filename||'kgg_trainingsplan.pdf';
    document.body.appendChild(a);
    a.click();
    setTimeout(()=>{URL.revokeObjectURL(url);a.remove();},1000);
  }
  function pdfBlobToBase64(blob){
    return new Promise((resolve,reject)=>{
      const reader=new FileReader();
      reader.onload=()=>resolve(String(reader.result||'').split(',')[1]||'');
      reader.onerror=()=>reject(reader.error||new Error('PDF konnte nicht gelesen werden.'));
      reader.readAsDataURL(blob);
    });
  }
  function nativePdfBridge(){
    return window.KGGNativePdf&&window.KGGNativePdf.available?window.KGGNativePdf:null;
  }
  async function sendPdfToNative(action){
    if(!currentPdfPreview||!currentPdfPreview.blob)return false;
    const bridge=nativePdfBridge();
    if(!bridge)return false;
    try{
      const base64=await pdfBlobToBase64(currentPdfPreview.blob);
      if(action==='download'&&typeof bridge.download==='function')return !!bridge.download(currentPdfPreview.filename,base64);
      if(action==='print'&&typeof bridge.print==='function')return !!bridge.print(currentPdfPreview.filename,base64);
      if(typeof bridge.open==='function')return !!bridge.open(currentPdfPreview.filename,base64);
    }catch(err){console.warn('Native PDF-Aktion fehlgeschlagen:',err);}
    return false;
  }
  let currentPdfPreview=null;
  let pdfPreviewFallbackTimer=null;
  function setPdfPreviewFallbackVisible(isVisible){
    const fallback=$('pdfPreviewFallback');
    if(fallback)fallback.classList.toggle('hidden',!isVisible);
  }
  function shouldUsePdfMobileBridge(){
    return !!(window.matchMedia && (window.matchMedia('(pointer: coarse)').matches || window.matchMedia('(max-width: 700px)').matches));
  }
  function setPdfMobileBridgeVisible(isVisible){
    const bridge=$('pdfPreviewMobileBridge');
    const modal=$('pdfPreviewModal');
    if(bridge)bridge.classList.toggle('hidden',!isVisible);
    if(modal)modal.classList.toggle('pdfPreviewModalMobile',isVisible);
  }
  function openPdfPreview(result){
    if(!result||!result.blob)return;
    if(currentPdfPreview&&currentPdfPreview.url)URL.revokeObjectURL(currentPdfPreview.url);
    if(pdfPreviewFallbackTimer)clearTimeout(pdfPreviewFallbackTimer);
    const url=URL.createObjectURL(result.blob);
    currentPdfPreview={url,blob:result.blob,filename:result.filename||'kgg_trainingsplan.pdf'};
```
