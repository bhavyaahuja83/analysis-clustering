"""
Self-contained Flask + Bootstrap web app to view clusters from `output_clusters.xlsx`.
Features:
- Hardcoded EXCEL_FILE = 'output_clusters.xlsx'
- Dark Bootstrap theme (Bootswatch 'darkly') via CDN
- Clusters are expandable; time slots shown as children
- Instant client-side filters (IncomeGroup, Profession)
- Ctrl+F opens floating search box (searches only inside expanded clusters)
- Highlights only matching substring using <mark>
- Shows match count and next/previous navigation (matches limited to expanded clusters)
- Copy-to-clipboard icon with Bootstrap toast notification

Run: python cluster_web_app.py
Open: http://127.0.0.1:5000

Requires: Flask, pandas
Install: pip install flask pandas
"""

from flask import Flask, render_template_string, jsonify, request
import pandas as pd
import json
import math

EXCEL_FILE = 'output_clusters.xlsx'

app = Flask(__name__)

# --------------------- Load and prepare data ---------------------

def safe_float(v):
    try:
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def load_and_group(path):
    df = pd.read_excel(path)
    grouped = {}
    for _, row in df.iterrows():
        cid = row.get('ClusterIndex')
        if pd.isna(cid):
            continue
        try:
            cid_key = str(int(cid))
        except Exception:
            cid_key = str(cid)
        if cid_key not in grouped:
            grouped[cid_key] = {
                'ClusterIndex': cid_key,
                'meta': {
                    'AgeGroup': str(row.get('AgeGroup', '')),
                    'Gender': str(row.get('Gender', '')),
                    'IncomeGroup': str(row.get('IncomeGroup', '')),
                    'Profession': str(row.get('Profession', '') or row.get('ProfessionType', '')),
                    'City': str(row.get('City', '')),
                    'Brand': str(row.get('Brand', '')),
                    'LeadCount': int(row.get('LeadCount', 0) if not pd.isna(row.get('LeadCount')) else 0)
                },
                'slots': []
            }
        grouped[cid_key]['slots'].append({
            'Day': str(row.get('Day', '')),
            'Time': str(row.get('Time', '')),
            'PickupRate': safe_float(row.get('PickupRate')),
            'AvgDuration': safe_float(row.get('AvgDuration')),
            'BestTime': str(row.get('BestTime', ''))
        })
    # Convert to list for stable ordering
    return sorted(grouped.values(), key=lambda x: int(x['ClusterIndex']) if x['ClusterIndex'].isdigit() else x['ClusterIndex'])

DATA = load_and_group(EXCEL_FILE)

# Extract distinct filter values
def get_filter_values(data):
    incomes = sorted({d['meta'].get('IncomeGroup','') for d in data if d['meta'].get('IncomeGroup','')})
    profs = sorted({d['meta'].get('Profession','') for d in data if d['meta'].get('Profession','')})
    return incomes, profs

INCOMES, PROFS = get_filter_values(DATA)

# --------------------- Templates ---------------------

INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cluster Viewer</title>
    <!-- Bootswatch Darkly -->
    <link href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css" rel="stylesheet">
    <style>
      body { padding: 18px; }
      .cluster-card { margin-bottom: 10px; border-radius: 8px; }
      .slot-row { padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }
      .slot-row:nth-child(odd){ background: rgba(255,255,255,0.02); }
      .slot-row:last-child{ border-bottom: none; }
      .meta-header { font-weight: 600; }
      .search-overlay { position: fixed; right: 24px; top: 24px; z-index: 1050; }
      .toast-container { position: fixed; bottom: 24px; right: 24px; z-index: 2000; }
      mark.match { background: #ffd54f; color: #000; padding: 0 2px; border-radius: 2px; }
      .copy-btn { cursor: pointer; }
      .collapsed .card-body { display: none; }
    </style>
  </head>
  <body>
    <div class="container-fluid">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>Cluster Viewer</h3>
        <div>
          <div class="input-group">
            <select id="filterIncome" class="form-select form-select-sm me-2">
              <option value="">All incomes</option>
              {% for v in incomes %}
              <option value="{{v}}">{{v}}</option>
              {% endfor %}
            </select>
            <select id="filterProf" class="form-select form-select-sm me-2">
              <option value="">All professions</option>
              {% for v in profs %}
              <option value="{{v}}">{{v}}</option>
              {% endfor %}
            </select>
            <button id="expandAll" class="btn btn-sm btn-outline-light me-1">Expand all</button>
            <button id="collapseAll" class="btn btn-sm btn-outline-light">Collapse all</button>
          </div>
        </div>
      </div>

      <div id="clusters">
        <!-- clusters rendered by JS -->
      </div>

      <!-- Search overlay -->
      <div class="search-overlay" id="searchOverlay" style="display:none;">
        <div class="input-group">
          <input id="searchInput" class="form-control form-control-sm" placeholder="Search in expanded clusters (Ctrl+F)" />
          <button id="prevMatch" class="btn btn-sm btn-outline-light">◀</button>
          <button id="nextMatch" class="btn btn-sm btn-outline-light">▶</button>
          <span class="badge bg-secondary ms-2" id="matchCount">0</span>
          <button id="closeSearch" class="btn btn-sm btn-outline-light ms-2">✖</button>
        </div>
      </div>

      <!-- Toast container -->
      <div class="toast-container" id="toastContainer"></div>

    </div>

    <script>
      // Data injected from server
      const DATA = {{ data | safe }};

      // Render clusters
      function renderClusters(data){
        const container = document.getElementById('clusters');
        container.innerHTML = '';
        data.forEach(cluster => {
          const cid = cluster.ClusterIndex;
          const meta = cluster.meta;
          const card = document.createElement('div');
          card.className = 'card bg-dark cluster-card';
          card.dataset.cid = cid;

          const header = document.createElement('div');
          header.className = 'card-header d-flex justify-content-between align-items-center';
          header.innerHTML = `
            <div>
              <span class='meta-header'>Cluster ${cid}</span>
              <small class='text-muted ms-2'>${meta.AgeGroup} · ${meta.Gender} · ${meta.City} · ${meta.Profession} · ${meta.IncomeGroup}</small>
            </div>
            <div>
              <button class='btn btn-sm btn-outline-light me-2 toggle-btn' data-bs-toggle='collapse' data-bs-target='#c${cid}'>Expand</button>
              <button class='btn btn-sm btn-secondary copy-cluster' data-cid='${cid}'>📋</button>
            </div>
          `;

          const body = document.createElement('div');
          body.className = 'card-body collapse';
          body.id = 'c' + cid;

          // slots
          cluster.slots.forEach((slot, i) => {
            const row = document.createElement('div');
            row.className = 'slot-row d-flex justify-content-between align-items-center';
            row.innerHTML = `
              <div>
                <div><strong>${slot.Day}</strong> · ${slot.Time}</div>
                <div class='text-muted small'>Pickup: ${slot.PickupRate || ''} · Avg: ${slot.AvgDuration || ''} s · Best: ${slot.BestTime || ''}</div>
              </div>
              <div>
                <button class='btn btn-sm btn-outline-light copy-slot' data-cid='${cid}' data-index='${i}'>📋</button>
              </div>
            `;
            body.appendChild(row);
          });

          card.appendChild(header);
          card.appendChild(body);
          container.appendChild(card);
        });
      }

      // initial render
      renderClusters(DATA);

      // Filters
      const filterIncome = document.getElementById('filterIncome');
      const filterProf = document.getElementById('filterProf');

      function applyFilters(){
        const inc = filterIncome.value;
        const prof = filterProf.value;
        const filtered = DATA.filter(c => {
          if(inc && c.meta.IncomeGroup !== inc) return false;
          if(prof && c.meta.Profession !== prof) return false;
          return true;
        });
        renderClusters(filtered);
      }

      filterIncome.addEventListener('change', applyFilters);
      filterProf.addEventListener('change', applyFilters);

      // Expand/Collapse all
      document.getElementById('expandAll').addEventListener('click', ()=>{
        document.querySelectorAll('.card-body.collapse').forEach(el=> bootstrap.Collapse.getOrCreateInstance(el).show());
      });
      document.getElementById('collapseAll').addEventListener('click', ()=>{
        document.querySelectorAll('.card-body.collapse').forEach(el=> bootstrap.Collapse.getOrCreateInstance(el).hide());
      });

      // Copy handlers with toast
      function showToast(msg){
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-bg-dark border-0 show';
        toast.role = 'alert';
        toast.ariaLive = 'assertive';
        toast.ariaAtomic = 'true';
        toast.innerHTML = `<div class='d-flex'><div class='toast-body'>${msg}</div><button type='button' class='btn-close btn-close-white me-2 m-auto' data-bs-dismiss='toast'></button></div>`;
        container.appendChild(toast);
        setTimeout(()=>{ toast.classList.remove('show'); toast.remove(); }, 1800);
      }

      document.addEventListener('click', function(e){
        if(e.target.matches('.copy-slot')){
          const cid = e.target.dataset.cid;
          const idx = parseInt(e.target.dataset.index);
          const cluster = DATA.find(c=>c.ClusterIndex===cid);
          if(cluster){
            const slot = cluster.slots[idx];
            const pickup = slot.PickupRate ? (slot.PickupRate + '%') : '';
            const duration = slot.AvgDuration ? (slot.AvgDuration + ' s') : '';
            const text = `Day: ${slot.Day} | Time: ${slot.Time} | Pickup Rate: ${pickup} | Avg Duration: ${duration} | Best Time: ${slot.BestTime}`;
            navigator.clipboard.writeText(text).then(()=> showToast('Time slot copied'));
          }
        }else if(e.target.matches('.copy-cluster')){
          const cid = e.target.dataset.cid;
          const cluster = DATA.find(c=>c.ClusterIndex===cid);
          if(cluster){
            const meta = cluster.meta;
            const text = Object.entries(meta).map(([k,v])=>`${k}: ${v}`).join(' | ');
            navigator.clipboard.writeText(text).then(()=> showToast('Cluster copied'));
          }
        }
      });

      // ------------------ Search (Ctrl+F like) ------------------
      const searchOverlay = document.getElementById('searchOverlay');
      const searchInput = document.getElementById('searchInput');
      const matchCount = document.getElementById('matchCount');
      const nextBtn = document.getElementById('nextMatch');
      const prevBtn = document.getElementById('prevMatch');
      const closeBtn = document.getElementById('closeSearch');

      let matches = []; // list of {el, start, end}
      let currentMatch = -1;

      function openSearch(){
        searchOverlay.style.display = 'block';
        searchInput.focus();
        searchInput.select();
      }
      function closeSearch(){
        searchOverlay.style.display = 'none';
        clearHighlights();
        matches = [];
        currentMatch = -1;
        matchCount.textContent = '0';
      }

      document.addEventListener('keydown', function(e){
        if((e.ctrlKey||e.metaKey) && e.key === 'f'){
          e.preventDefault();
          openSearch();
        } else if(e.key === 'Escape'){
          closeSearch();
        }
      });

      function clearHighlights(){
        document.querySelectorAll('mark.match').forEach(m=>{
          const parent = m.parentNode;
          parent.replaceChild(document.createTextNode(m.textContent), m);
          parent.normalize();
        });
      }

      function doSearch(){
        clearHighlights();
        matches = [];
        currentMatch = -1;
        const term = searchInput.value.trim();
        if(!term) { matchCount.textContent = '0'; return; }
        // search only within expanded clusters (collapsed ones have no .show)
        document.querySelectorAll('.card-body.collapse.show').forEach(body=>{
          // find text nodes under body
          const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, null);
          const nodes = [];
          while(walker.nextNode()) nodes.push(walker.currentNode);
          nodes.forEach(node=>{
            const txt = node.nodeValue;
            const idx = txt.toLowerCase().indexOf(term.toLowerCase());
            if(idx !== -1){
              // replace matching substring with <mark>
              const span = document.createElement('span');
              const before = txt.slice(0, idx);
              const match = txt.slice(idx, idx+term.length);
              const after = txt.slice(idx+term.length);
              const frag = document.createDocumentFragment();
              if(before) frag.appendChild(document.createTextNode(before));
              const mk = document.createElement('mark'); mk.className='match'; mk.textContent = match; frag.appendChild(mk);
              if(after) frag.appendChild(document.createTextNode(after));
              node.parentNode.replaceChild(frag, node);
              matches.push({el: mk});
            }
          });
        });
        matchCount.textContent = `${matches.length}`;
        if(matches.length) { currentMatch = 0; scrollToMatch(0); }
      }

      function scrollToMatch(i){
        if(matches.length===0) return;
        currentMatch = (i + matches.length) % matches.length;
        const el = matches[currentMatch].el;
        el.scrollIntoView({behavior:'smooth', block:'center'});
        // flash
        el.classList.add('bg-warning');
        setTimeout(()=> el.classList.remove('bg-warning'), 800);
      }

      searchInput.addEventListener('input', function(){ doSearch(); });
      nextBtn.addEventListener('click', function(){ if(matches.length) scrollToMatch(currentMatch+1); });
      prevBtn.addEventListener('click', function(){ if(matches.length) scrollToMatch(currentMatch-1); });
      closeBtn.addEventListener('click', closeSearch);

      // when cluster is toggled, re-run search so only expanded considered
      document.addEventListener('click', function(e){
        if(e.target.matches('.toggle-btn')){
          // small delay to allow bootstrap collapse to toggle
          setTimeout(()=>{ if(searchOverlay.style.display!=='none') doSearch(); }, 220);
        }
      });

      // Ensure bootstrap JS is available (bundle loaded at end)
    </script>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
"""

# --------------------- Routes ---------------------

@app.route('/')
def index():
    # pass DATA, INCOMES, PROFS to template
    return render_template_string(INDEX_HTML, data=json.dumps(DATA), incomes=INCOMES, profs=PROFS)

@app.route('/data')
def data_api():
    return jsonify(DATA)

# --------------------- Run ---------------------

if __name__ == '__main__':
    app.run(debug=True)
