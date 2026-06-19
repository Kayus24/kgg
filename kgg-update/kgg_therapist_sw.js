/* KGG therapist service worker
 * v004 phone-only admin banner cleanup
 * Scope: kgg-update only. Does not touch PDF, QR, patient app, scan, parser, plan state or storage.
 */
const KGG_SW_VERSION='v004-phone-admin-banner-clean';
const PATCH_ID='kgg-mini-patch-v400-08-phone-hide-admin-file-banner';
const PATCH_STYLE=`
<style id="${PATCH_ID}">
  /* v004: hide internal ADMIN-DATEI/Admin-Test banner in phone layout only. */
  @media (max-width:759px){
    .adminTestBanner{
      display:none!important;
    }
  }
</style>
`;

self.addEventListener('install',()=>{
  self.skipWaiting();
});

self.addEventListener('activate',event=>{
  event.waitUntil(self.clients.claim());
});

self.addEventListener('message',event=>{
  if(event.data&&event.data.type==='SKIP_WAITING'){
    self.skipWaiting();
  }
});

function shouldPatchHtml(request){
  try{
    const url=new URL(request.url);
    const path=url.pathname;
    return request.mode==='navigate' || path.endsWith('/kgg-update/') || path.endsWith('/kgg-update/index.html');
  }catch(_err){
    return false;
  }
}

async function patchHtmlResponse(request){
  const response=await fetch(request,{cache:'no-store'});
  const contentType=response.headers.get('content-type')||'';
  if(!contentType.includes('text/html'))return response;

  let html=await response.text();
  if(!html.includes(PATCH_ID)){
    if(html.includes('</head>')){
      html=html.replace('</head>',PATCH_STYLE+'\n</head>');
    }else{
      html=PATCH_STYLE+html;
    }
  }

  const headers=new Headers(response.headers);
  headers.set('content-type','text/html; charset=utf-8');
  headers.set('cache-control','no-store');
  return new Response(html,{
    status:response.status,
    statusText:response.statusText,
    headers
  });
}

self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  if(!shouldPatchHtml(event.request))return;
  event.respondWith(patchHtmlResponse(event.request));
});
