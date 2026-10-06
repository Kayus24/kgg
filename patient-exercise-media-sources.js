(()=>{
  const VERSION='exercise-media-sources-v2-license-checked';
  if(window.KGGExerciseMediaSources&&window.KGGExerciseMediaSources.version===VERSION)return;
  const REPDB='https://exercise-dataset.com/images/flat/';
  const WG='https://raw.githubusercontent.com/bryllim/workout-guide/aac599224bb9780305239607ef98540b7e0ce389/packages/workout-guide/assets/';
  const EVER='https://raw.githubusercontent.com/everkinetic/data/446bb9a3d0c3beb6b84f7c9d77dfc8af707a2ab6/dist/svg/';
  const norm=value=>String(value||'').trim().toLocaleLowerCase('de-DE').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,' ').trim();
  const meta={
    repdb:{source:'RepDB',license:'RepDB Free Tier v1.0 · attribution required',credit:'Exercise data by RepDB (repdb.co)',url:'https://exercise-dataset.com/',licenseUrl:'https://github.com/RepDB/exercise-dataset/blob/main/LICENSE-DATA.md',checkedAt:'2026-10-05'},
    workoutGuide:{source:'Workout Guide',license:'CC BY-SA 4.0',credit:'Workout Guide · CC BY-SA 4.0',url:'https://bryllim.github.io/workout-guide/',licenseUrl:'https://github.com/bryllim/workout-guide/blob/main/LICENSE-ASSETS',checkedAt:'2026-10-05'},
    everkinetic:{source:'Everkinetic',license:'CC BY-SA 4.0',credit:'Everkinetic · CC BY-SA 4.0',url:'https://github.com/everkinetic/data',licenseUrl:'https://github.com/everkinetic/data/blob/master/LICENSE.md',checkedAt:'2026-10-05'}
  };
  const item=(source,id,url,mime,position)=>({id:'catalog:'+source+':'+id,type:'image',src:url,downloadUrl:url,mime,position,sourceMeta:{...meta[source]}});
  const repdb=(slug)=>[
    item('repdb',slug+':start',REPDB+slug+'-start.webp','image/webp','start'),
    item('repdb',slug+':peak',REPDB+slug+'-peak.webp','image/webp','peak')
  ];
  const workout=(slug)=>[
    item('workoutGuide',slug+':1',WG+slug+'/frame-1.svg','image/svg+xml','start'),
    item('workoutGuide',slug+':2',WG+slug+'/frame-2.svg','image/svg+xml','peak')
  ];
  const ever=(asset)=>[item('everkinetic',asset,EVER+asset+'.svg','image/svg+xml','main')];
  const defs=[
    {source:'repdb',names:['Beinpresse','Leg Press'],media:repdb('leg-press')},
    {source:'repdb',names:['Rudern sitzend','Sitzendes Kabelrudern','Seated Cable Row','Rudern'],media:repdb('seated-cable-row')},
    {source:'repdb',names:['Brustpresse Maschine','Brustpresse','Machine Chest Press'],media:repdb('chest-press-machine')},
    {source:'workoutGuide',names:['Schulterdrücken','Schulterdruecken','Machine Shoulder Press'],media:workout('machine-shoulder-press')},
    {source:'workoutGuide',names:['Latzug','Lat Pulldown'],media:workout('lat-pulldown')},
    {source:'workoutGuide',names:['Beinbeuger sitzend','Seated Leg Curl'],media:workout('seated-leg-curl')},
    {source:'workoutGuide',names:['Plank','Unterarmstütz','Unterarmstuetz'],media:workout('plank')},
    {source:'everkinetic',names:['Seitstütz mit Hüftsenken','Seitstuetz mit Hueftsenken','Side Plank Hip Dips'],media:ever('0113-tension')},
    {source:'workoutGuide',names:['Rückenstrecker','Rueckenstrecker','Back Extension'],media:workout('back-extension')},
    {source:'workoutGuide',names:['Beinschwünge','Beinschwuenge','Leg Swings'],media:workout('leg-swings-stretch')}
  ];
  const index=new Map();
  defs.forEach(def=>def.names.forEach(name=>index.set(norm(name),def)));
  const clone=value=>JSON.parse(JSON.stringify(value));
  function lookup(name){const def=index.get(norm(name));return def?clone(def.media):[]}
  function describe(name){const def=index.get(norm(name));return def?{source:meta[def.source].source,license:meta[def.source].license,credit:meta[def.source].credit,url:meta[def.source].url}:null}
  function audit(){const out={repdb:0,workoutGuide:0,everkinetic:0,mappings:defs.length};defs.forEach(def=>{if(def.source in out)out[def.source]++});return out}
  window.KGGExerciseMediaSources={version:VERSION,lookup,describe,audit,normalize:norm};
})();