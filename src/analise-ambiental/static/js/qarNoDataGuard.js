// static/js/qarNoDataGuard.js
(function () {
  const CSV_URL    = "/database_resumido.csv";
  const DATE_ID    = "input_date";
  const HOUR_ID    = "input_hour";
  const STATION_ID = "station";

  // --- CSS (grayscale, hide, clearing/opacity) ---
  (function injectCss(){
    const css = `
      .qar-gray{filter:grayscale(1) brightness(.82) contrast(.95);opacity:.75;transition:.2s}
      .qar-hide{display:none !important}
      .qar-clearing{opacity:0 !important; transition:opacity .15s linear}
    `;
    const s=document.createElement("style"); s.textContent=css; document.head.appendChild(s);
  })();

  // ---- helpers DOM ----
  const tsSelecionado = () => {
    const d = document.getElementById(DATE_ID)?.value || "";
    if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return null;
    const h = String(document.getElementById(HOUR_ID)?.value || "").split(":")[0].padStart(2,"0");
    return `${d} ${h}:30:00`;
  };
  const estacao = () => (document.getElementById(STATION_ID)?.value || "").toUpperCase();
  const poluenteAtivo = () =>
    document.getElementById("btn-pts")?.classList.contains("selected") ? "PTS" :
    document.getElementById("btn-mp10")?.classList.contains("selected") ? "MP10" : "MP2.5";

  const sphereNodes = () => {
    const sels=["#sphere",".sphere","[data-sphere]","#sphere-container canvas","canvas"];
    for (const s of sels){ const n=document.querySelectorAll(s); if(n.length) return Array.from(n); }
    return [];
  };
  const grayOn   = () => sphereNodes().forEach(el=>el.classList.add("qar-gray"));
  const grayOff  = () => sphereNodes().forEach(el=>el.classList.remove("qar-gray"));
  const clearOn  = () => sphereNodes().forEach(el=>el.classList.add("qar-clearing"));   // apaga visualmente
  const clearOff = () => sphereNodes().forEach(el=>el.classList.remove("qar-clearing")); // volta a aparecer

  // ---- mutadores dos painéis ----
  function setText(p, txt){ if(!p) return; if(!p.dataset.prevText) p.dataset.prevText=p.textContent; p.textContent=txt; }
  function restoreText(p){ if(!p) return; if(p.dataset.prevText){ p.textContent=p.dataset.prevText; delete p.dataset.prevText; } }

  function applyNoDataOnPanel(pol){
    // esconder bloco da direita e barra
    document.getElementById("classification-meaning")?.classList.add("qar-hide");
    document.getElementById("classification-bar")?.classList.add("qar-hide");

    if (pol === "PTS") {
      const p = document.querySelector("#basic-info-pts p");
      setText(p, "Média das últimas 24h: Não há registros suficientes.");
      return;
    }
    const panelId = pol==="MP10" ? "basic-info-mp10" : "basic-info-mp2_5";
    const ps = Array.from(document.querySelectorAll(`#${panelId} p`));
    const pMedia = ps.find(x => /^Média das últimas 24h:/i.test(x.textContent||""));
    const pIqar  = ps.find(x => /IQAr:/i.test(x.textContent||""));
    const pClass = ps.find(x => /^Classificação:/i.test(x.textContent||""));
    pMedia?.classList.add("qar-hide");
    pClass?.classList.add("qar-hide");
    if (pIqar) setText(pIqar, "IQAr: Não há registros suficientes.");
    // esconde “Mais detalhes”
    document.querySelector(`#${panelId} a[id^="more-details-link"]`)?.classList.add("qar-hide");
    document.querySelector(`#${panelId} .details-container`)?.classList.add("qar-hide");
  }

  function clearNoDataOnPanel(pol){
    // mostrar bloco da direita e barra
    document.getElementById("classification-meaning")?.classList.remove("qar-hide");
    document.getElementById("classification-bar")?.classList.remove("qar-hide");

    if (pol === "PTS") {
      const p = document.querySelector("#basic-info-pts p");
      restoreText(p);
      return;
    }
    const panelId = pol==="MP10" ? "basic-info-mp10" : "basic-info-mp2_5";
    const ps = Array.from(document.querySelectorAll(`#${panelId} p`));
    const pMedia = ps.find(x => x.classList.contains("qar-hide") || /^Média das últimas 24h:/.test(x.dataset?.prevText||""));
    const pClass = ps.find(x => x.classList.contains("qar-hide") || /^Classificação:/.test(x.dataset?.prevText||""));
    const pIqar  = ps.find(x => /IQAr:/.test(x.textContent||""));
    pMedia?.classList.remove("qar-hide");
    pClass?.classList.remove("qar-hide");
    restoreText(pIqar);
    document.querySelector(`#${panelId} a[id^="more-details-link"]`)?.classList.remove("qar-hide");
    document.querySelector(`#${panelId} .details-container`)?.classList.remove("qar-hide");
  }

  // ---- CSV ----
  let DB=null, LOADING=null;
  async function loadCsv(){
    if (DB) return DB;
    if (LOADING) return LOADING;
    LOADING=(async()=>{
      const txt = await fetch(CSV_URL,{cache:"no-store"}).then(r=>r.text());
      const lines = txt.split(/\r?\n/).filter(Boolean);
      const header = lines[0].split(",");
      if (header[0] && header[0].charCodeAt(0)===0xFEFF) header[0]=header[0].slice(1);
      const mapCol=new Map(header.map((h,i)=>[h,i]));
      const rows=new Map();
      for(let i=1;i<lines.length;i++){ const p=lines[i].split(","); if(p.length) rows.set(p[0], p); }
      DB={header,mapCol,rows}; LOADING=null; return DB;
    })();
    return LOADING;
  }
  const insuf = v => v==null || (String(v).trim()==="") || (String(v).trim().toLowerCase()==="n") || /dados\s+insuficientes/i.test(String(v));
  const cell  = (row,key,idx)=>{ const i=idx.get(key); return i==null?null:row[i]; };

  // ---- check principal ----
  async function check(){
    const db = await loadCsv();
    const ts = tsSelecionado(); if(!ts) { clearOff(); return; }
    const st = estacao();
    const pol= poluenteAtivo();

    const row = db.rows.get(ts);
    if (!row){
      grayOn(); applyNoDataOnPanel(pol); clearOff(); return;
    }

    let noData;
    if (pol==="PTS"){
      noData = insuf(cell(row, `${st}_PTS_media`, db.mapCol));
    } else {
      const base = `${st}_${pol}`;
      noData = [ `${base}_media`, `${base}_IQAr`, `${base}_class` ]
        .some(k => insuf(cell(row,k,db.mapCol)));
    }

    if (noData){ grayOn();  applyNoDataOnPanel(pol); }
    else       { grayOff(); clearNoDataOnPanel(pol); }
    clearOff(); // garante que a esfera volte a aparecer após a verificação
  }

  // ---- eventos ----
  function wire(){
    const fire = ()=>{ clearOn(); check(); }; // apaga visualmente e reavalia

    ["change","input"].forEach(evt=>{
      document.getElementById(DATE_ID)?.addEventListener(evt, fire);
      document.getElementById(HOUR_ID)?.addEventListener(evt, fire);
      document.getElementById(STATION_ID)?.addEventListener(evt, fire);
    });

    // botões de poluente — só reavalia
    document.getElementById("btn-pts")?.addEventListener("click", ()=>setTimeout(check,0));
    document.getElementById("btn-mp2_5")?.addEventListener("click", ()=>setTimeout(check,0));
    document.getElementById("btn-mp10")?.addEventListener("click", ()=>setTimeout(check,0));
  }

  document.addEventListener("DOMContentLoaded", ()=>{ wire(); loadCsv().then(check); });

  // Recheca e libera a esfera após qualquer fetch que atualize os painéis
  const _fetch = window.fetch.bind(window);
  window.fetch = async function(input, init){
    const res = await _fetch(input, init);
    try {
      clearOff();
      setTimeout(check,0);
    } catch {}
    return res;
  };
})();
