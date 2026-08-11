<!-- KGG PATCH START kgg-v021-embed-jsqr-gallery-decode wrapper -->
<script id="kgg-v021-embed-jsqr-gallery-decode-wrapper">

(function(){
  var oldDetect = window.detectQrOnCanvas;
  function getImageData(canvas){
    try{
      var ctx = canvas && canvas.getContext && canvas.getContext('2d',{willReadFrequently:true});
      return ctx ? ctx.getImageData(0,0,canvas.width,canvas.height) : null;
    }catch(e){ return null; }
  }
  function jsqrFallback(canvas){
    if(!canvas || typeof window.jsQR !== 'function') return '';
    var img = getImageData(canvas);
    if(!img) return '';
    try{
      var hit = window.jsQR(img.data, canvas.width, canvas.height, {inversionAttempts:'attemptBoth'});
      return hit && hit.data ? String(hit.data) : '';
    }catch(e){ return ''; }
  }
  async function wrappedDetect(canvas, detector){
    if(typeof oldDetect === 'function' && oldDetect !== wrappedDetect){
      try{
        var oldResult = await oldDetect(canvas, detector);
        if(oldResult) return oldResult;
      }catch(e){}
    }
    return jsqrFallback(canvas);
  }
  try{ window.detectQrOnCanvas = wrappedDetect; }catch(e){}
  try{ detectQrOnCanvas = wrappedDetect; }catch(e){}
  window.KGG_QR_GALLERY_DEBUG = {
    patchId: 'kgg-v021-embed-jsqr-gallery-decode',
    check: function(){ return { patchId:this.patchId, jsQR:typeof window.jsQR==='function', detectQrOnCanvas:typeof window.detectQrOnCanvas }; }
  };
})();

</script>
<!-- KGG PATCH END kgg-v021-embed-jsqr-gallery-decode wrapper -->

