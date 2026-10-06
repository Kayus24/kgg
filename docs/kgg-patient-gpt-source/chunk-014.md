# KGG Patient Source Chunk 014

- Source file: `patient-install-prompt.js`
- Characters: 1-2938
- Full source SHA-256: `2b985490a16c26cf7edcacc29cd62905f8cdb5d6c17fa31fb8fa1adb9ba3eaac`

```
(()=>{
  const VERSION='install-prompt-v2-capability-only';
  const KEY='__kggInstallPrompt';
  if(window.__kggInstallPromptPatch===VERSION)return;
  window.__kggInstallPromptPatch=VERSION;

  function getPrompt(){return window[KEY]||null}
  function setPrompt(prompt){window[KEY]=prompt||null;return window[KEY]}
  function clearPrompt(prompt){if(!prompt||getPrompt()===prompt)setPrompt(null)}
  function capturePrompt(event){
    if(!event)return null;
    try{event.preventDefault()}catch(e){}
    setPrompt(event);
    const isStandalone=typeof window.standalone==='function'&&window.standalone();
    if(isStandalone){clearPrompt(event);hideInstallUi();return null}
    const row=document.getElementById('installSmall'),text=document.getElementById('installOfferText'),button=document.getElementById('installOfferBtn');if(row)row.classList.remove('hide');if(text)text.classList.remove('hide');if(button)button.classList.remove('hide');
    if(typeof window.maybeAskInstall==='function')window.maybeAskInstall();
    return event
  }
  async function consumePrompt(prompt){
    const active=prompt||getPrompt();
    if(!active||typeof active.prompt!=='function')return {handled:false,choice:null};
    clearPrompt(active);
    try{
      await active.prompt();
      const choice=active.userChoice&&typeof active.userChoice.then==='function'?await active.userChoice:null;
      return {handled:true,choice};
    }catch(error){
      return {handled:true,choice:null,error};
    }finally{
      clearPrompt(active)
    }
  }
  function hideInstallUi(){
    const box=document.getElementById('installBox'),text=document.getElementById('installOfferText'),button=document.getElementById('installOfferBtn'),hint=document.getElementById('installHint');
    if(box)box.classList.add('hide');if(text)text.classList.add('hide');if(button)button.classList.add('hide');if(hint){hint.classList.add('hide');hint.innerHTML=''}
  }
  function patchInstallApp(){
    if(window.__kggSharedInstallAppPatched||typeof window.installApp!=='function')return;
    window.installApp=async function(){
      const prompt=getPrompt();
      if(!prompt||typeof prompt.prompt!=='function'){hideInstallUi();return {handled:false,choice:null}}
      const result=await consumePrompt(prompt);hideInstallUi();return result
    };
    window.__kggSharedInstallAppPatched=1
  }
  function bind(){
    if(!window.__kggInstallPromptListenerBound){
      window.__kggInstallPromptListenerBound=1;
      window.addEventListener('beforeinstallprompt',capturePrompt);window.addEventListener('appinstalled',()=>{setPrompt(null);hideInstallUi()})
    }
    patchInstallApp()
  }
  function init(){bind();setTimeout(bind,250);setTimeout(bind,900)}
  if(window.__KGG_TEST__)window.__kggInstallPromptTest={getPrompt,setPrompt,clearPrompt,capturePrompt,consumePrompt};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init()
})();
```
