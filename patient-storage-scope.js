(()=>{
  const REQUEST_ID_RE=/\/previews\/([a-z0-9][a-z0-9-]{5,63})(?:\/|$)/i;
  const match=String(location.pathname||'').match(REQUEST_ID_RE);
  const requestId=match?decodeURIComponent(match[1]).toLowerCase():'';
  if(!requestId)return;

  const prefix='preview:'+requestId+':';
  const methodNames=new Set(['clear','getItem','key','removeItem','setItem']);
  const nativeMethods={
    clear:Storage.prototype.clear,
    getItem:Storage.prototype.getItem,
    key:Storage.prototype.key,
    removeItem:Storage.prototype.removeItem,
    setItem:Storage.prototype.setItem,
  };
  const nativeStorages=new WeakSet();
  const proxyToNative=new WeakMap();
  let localNative;
  let sessionNative;
  try{
    localNative=window.localStorage;
    sessionNative=window.sessionStorage;
    nativeStorages.add(localNative);
    nativeStorages.add(sessionNative);
  }catch(e){return}

  const nativeFor=receiver=>proxyToNative.get(receiver)||receiver;
  const scopedReceiver=receiver=>nativeStorages.has(nativeFor(receiver));
  const storageKey=key=>{
    const name=String(key);
    return name.startsWith(prefix)?name:prefix+name;
  };
  const visibleKeys=receiver=>{
    const native=nativeFor(receiver),keys=[];
    if(!nativeStorages.has(native))return keys;
    for(let index=0;index<native.length;index+=1){
      const key=nativeMethods.key.call(native,index);
      if(key&&key.startsWith(prefix))keys.push(key.slice(prefix.length));
    }
    return keys;
  };
  const getItem=(receiver,key)=>{
    const native=nativeFor(receiver);
    return scopedReceiver(receiver)?nativeMethods.getItem.call(native,storageKey(key)):nativeMethods.getItem.call(native,key);
  };
  const setItem=(receiver,key,value)=>{
    const native=nativeFor(receiver);
    return nativeMethods.setItem.call(native,scopedReceiver(receiver)?storageKey(key):key,value);
  };
  const removeItem=(receiver,key)=>{
    const native=nativeFor(receiver);
    return nativeMethods.removeItem.call(native,scopedReceiver(receiver)?storageKey(key):key);
  };
  const clear=(receiver)=>{
    const native=nativeFor(receiver);
    if(!scopedReceiver(receiver))return nativeMethods.clear.call(native);
    visibleKeys(native).forEach(key=>nativeMethods.removeItem.call(native,storageKey(key)));
  };
  const key=(receiver,index)=>{
    const keys=visibleKeys(receiver);
    return keys[Number(index)]??null;
  };

  Storage.prototype.getItem=function(name){return getItem(this,name)};
  Storage.prototype.setItem=function(name,value){return setItem(this,name,value)};
  Storage.prototype.removeItem=function(name){return removeItem(this,name)};
  Storage.prototype.clear=function(){return clear(this)};
  Storage.prototype.key=function(index){return key(this,index)};

  function createScopedStorage(native){
    const proxy=new Proxy(native,{
      get(target,name,receiver){
        if(name==='length')return visibleKeys(receiver).length;
        if(typeof name==='symbol'||methodNames.has(name))return Reflect.get(target,name,receiver);
        return getItem(receiver,name);
      },
      set(target,name,value,receiver){
        if(typeof name==='symbol'||methodNames.has(name)||name==='length')return Reflect.set(target,name,value,receiver);
        setItem(receiver,name,value);
        return true;
      },
      deleteProperty(target,name){
        if(typeof name==='symbol'||methodNames.has(name)||name==='length')return false;
        removeItem(proxy,name);
        return true;
      },
      ownKeys(target){return visibleKeys(proxy)},
      has(target,name){
        if(typeof name==='symbol'||methodNames.has(name)||name==='length')return name in target;
        return getItem(proxy,name)!==null;
      },
      getOwnPropertyDescriptor(target,name){
        if(typeof name==='string'&&getItem(proxy,name)!==null){
          return {configurable:true,enumerable:true,value:getItem(proxy,name),writable:true};
        }
        return Reflect.getOwnPropertyDescriptor(target,name);
      },
    });
    proxyToNative.set(proxy,native);
    return proxy;
  }

  try{
    Object.defineProperty(window,'localStorage',{configurable:true,value:createScopedStorage(localNative)});
    Object.defineProperty(window,'sessionStorage',{configurable:true,value:createScopedStorage(sessionNative)});
    window.__KGG_STORAGE_SCOPE__={kind:'preview',requestId,prefix};
  }catch(e){
    window.__KGG_STORAGE_SCOPE__={kind:'preview',requestId,prefix,error:'scope-install-failed'};
  }
})();
