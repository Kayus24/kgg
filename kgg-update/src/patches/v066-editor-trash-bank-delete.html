<!-- KGG PATCH START kgg-v066-editor-trash-bank-delete -->
<!-- Editor-Mülleimer löscht immer aus Übungsdatenbank -->
<script id="kgg-v066-editor-trash-bank-delete">
(function(){
  'use strict';
  const PATCH_ID='kgg-v066-editor-trash-bank-delete';
  const deleteButton=document.getElementById('deleteExercise');
  if(!deleteButton||typeof deleteButton.onclick!=='function')return;

  const originalDeleteHandler=deleteButton.onclick;
  let lastPlanEditId='';

  document.addEventListener('click',function(ev){
    const target=ev.target&&ev.target.closest?ev.target.closest('[data-planedit]'):null;
    if(target)lastPlanEditId=String(target.dataset.planedit||'');
  },true);

  function normalizedName(value){
    return String(value||'').trim().toLocaleLowerCase('de-DE');
  }

  function currentPlanExercise(){
    const store=window.KGGDataStore;
    const plan=store&&typeof store.getCurrentPlan==='function'?store.getCurrentPlan():null;
    const exercises=plan&&Array.isArray(plan.exercises)?plan.exercises:[];
    if(lastPlanEditId){
      const byId=exercises.find(function(ex){
        return String(ex&&ex.localId||ex&&ex.id||'')===lastPlanEditId;
      });
      if(byId)return byId;
    }
    const editName=document.getElementById('editName');
    const name=normalizedName(editName&&editName.value);
    if(!name)return null;
    return exercises.find(function(ex){return normalizedName(ex&&ex.name)===name;})||null;
  }

  function findBankEditButton(bankId,name){
    const root=document.getElementById('bankContent');
    if(!root)return null;
    const buttons=Array.from(root.querySelectorAll('[data-edit]'));
    if(bankId){
      const byId=buttons.find(function(button){return String(button.dataset.edit||'')===String(bankId);});
      if(byId)return byId;
    }
    const wanted=normalizedName(name);
    if(!wanted)return null;
    return buttons.find(function(button){
      const row=button.closest('.bankItem,.bankRow,.bankExercise,[data-bank-id]')||button.parentElement;
      return normalizedName(row&&row.textContent).includes(wanted);
    })||null;
  }

  function stageFullBankList(){
    const input=document.getElementById('exerciseInput');
    const toggle=document.getElementById('bankToggle');
    const content=document.getElementById('bankContent');
    const savedValue=input?input.value:'';
    const savedStart=input&&typeof input.selectionStart==='number'?input.selectionStart:null;
    const savedEnd=input&&typeof input.selectionEnd==='number'?input.selectionEnd:null;
    const wasHidden=!!(content&&content.classList.contains('hidden'));
    let toggleCount=0;

    if(input)input.value='';
    if(toggle){
      if(wasHidden){
        toggle.click();
        toggleCount=1;
      }else{
        toggle.click();
        toggle.click();
        toggleCount=2;
      }
    }

    return function restoreBankView(){
      if(input){
        input.value=savedValue;
        if(savedStart!==null&&savedEnd!==null){
          try{input.setSelectionRange(savedStart,savedEnd);}catch(err){}
        }
      }
      if(toggle){
        for(let i=0;i<toggleCount;i++)toggle.click();
      }
    };
  }

  function routeTrashToBankDelete(){
    if(deleteButton.dataset.scope==='bank'){
      originalDeleteHandler.call(deleteButton);
      return;
    }

    const planExercise=currentPlanExercise();
    const bankId=planExercise&&String(planExercise.bankId||planExercise.sourceId||'');
    const name=planExercise&&planExercise.name||
      (document.getElementById('editName')&&document.getElementById('editName').value)||'';

    let bankEdit=findBankEditButton(bankId,name);
    let restore=function(){};
    if(!bankEdit){
      restore=stageFullBankList();
      bankEdit=findBankEditButton(bankId,name);
    }

    if(!bankEdit){
      restore();
      alert('Diese Übung ist nicht in der Übungsdatenbank gespeichert.');
      return;
    }

    bankEdit.click();
    originalDeleteHandler.call(deleteButton);
    restore();
  }

  deleteButton.setAttribute('aria-label','Aus Übungsdatenbank löschen');
  deleteButton.setAttribute('title','Aus Übungsdatenbank löschen');
  deleteButton.onclick=function(ev){
    if(ev){
      ev.preventDefault();
      ev.stopPropagation();
    }
    routeTrashToBankDelete();
  };
  deleteButton.dataset.kggDeleteTarget='exercise-bank';

  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true};
})();
</script>
<!-- KGG PATCH END kgg-v066-editor-trash-bank-delete -->
