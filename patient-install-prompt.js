(()=>{
  const VERSION='install-prompt-v1-shared-reference';
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
    const button=document.getElementById('installSmall');
    if(button&&typeof standalone==='function'&&!standalone())button.classList.remove('hide');
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
  function hideInstallBox(){
    const box=document.getElementById('installBox');
    if(box)box.classList.add('hide')
  }
  function patchInstallApp(){
    if(window.__kggSharedInstallAppPatched||typeof window.installApp!=='function')return;
    const fallback=window.installApp;
    window.installApp=async function(){
      const prompt=getPrompt();
      if(prompt){
        const result=await consumePrompt(prompt);
        hideInstallBox();
        return result
      }
      return fallback.apply(this,arguments)
    };
    window.__kggSharedInstallAppPatched=1
  }
  function bind(){
    if(!window.__kggInstallPromptListenerBound){
      window.__kggInstallPromptListenerBound=1;
      window.addEventListener('beforeinstallprompt',capturePrompt)
    }
    patchInstallApp()
  }
  function init(){bind();setTimeout(bind,250);setTimeout(bind,900)}
  if(window.__KGG_TEST__)window.__kggInstallPromptTest={getPrompt,setPrompt,clearPrompt,capturePrompt,consumePrompt};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init()
})();
