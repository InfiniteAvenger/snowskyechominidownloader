/* ═══════════════════════════════════════════
   Snowsky Echo — Frontend
   ═══════════════════════════════════════════ */

const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

// ── Helpers ──

function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 3000);
}

async function api(path, body) {
  const r = await fetch('/api' + path, {
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  return r.json();
}

function esc(s) {
  const el = document.createElement('span');
  el.textContent = s || '';
  return el.innerHTML;
}

// SVG icons (inline for speed)
const ICONS = {
  play:     '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21"/></svg>',
  download: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
  list:     '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
  zip:      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 8v13H3V8"/><path d="M1 3h22v5H1z"/><path d="M10 12h4"/></svg>',
  chevronDown: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transition:transform .25s ease"><polyline points="6 9 12 15 18 9"/></svg>',
  check:    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  clock:    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
};

const LOGOS = {
  deezer:   '<svg viewBox="0 0 576 512" fill="currentColor"><path d="M451.46,244.71H576V172H451.46Zm0-173.89v72.67H576V70.82Zm0,275.06H576V273.2H451.46ZM0,447.09H124.54V374.42H0Zm150.47,0H275V374.42H150.47Zm150.52,0H425.53V374.42H301Zm150.47,0H576V374.42H451.46ZM301,345.88H425.53V273.2H301Zm-150.52,0H275V273.2H150.47Zm0-101.17H275V172H150.47Z"/></svg>',
  youtube:  '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.163a3.003 3.003 0 0 0-2.11-2.108C19.52 3.5 12 3.5 12 3.5s-7.52 0-9.388.555a3.002 3.002 0 0 0-2.11 2.108C0 8.03 0 12 0 12s0 3.97.502 5.837a3.003 3.003 0 0 0 2.11 2.108C4.48 20.5 12 20.5 12 20.5s7.52 0 9.388-.555a3.003 3.003 0 0 0 2.11-2.108C24 15.97 24 12 24 12s0-3.97-.502-5.837zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
  soulseek: '<svg viewBox="0 0 500 498" fill="currentColor"><path d="m 276.63897,193.26805 c -3.53902,18.87479 24.77316,24.77316 24.77316,24.77316 0,0 17.69512,4.7187 71.96014,-25.95283 54.26502,-30.67154 79.03818,-56.62437 79.03818,-56.62437 l -8.25772,18.87479 12.97642,-1.17968 -8.25772,16.51544 h 10.61706 l -12.97641,18.87479 5.89837,3.53903 -15.33577,16.51544 3.53903,7.07804 c 0,0 -23.59349,29.49186 -50.726,49.54633 -27.13251,20.05446 -40.10893,35.39023 -94.37395,66.06176 -27.13251,38.92926 -125.04548,117.96744 -125.04548,117.96744 l 3.53902,-18.87479 c 0,0 -10.61707,3.53902 -31.85121,12.97642 -1.17967,-9.4374 5.89838,-17.69512 5.89838,-17.69512 0,0 -3.53903,3.53902 -34.21056,12.97642 8.25772,-14.15609 15.33577,-20.05447 15.33577,-20.05447 0,0 -15.33577,3.53903 -31.851214,8.25772 1.17967,-16.51544 36.569904,-30.67153 36.569904,-30.67153 0,0 -9.43739,4.7187 -28.31218,4.7187 18.87479,-23.59349 82.5772,-48.36665 82.5772,-48.36665 0,0 21.23414,-22.41381 3.53903,-28.31219 -17.69512,-5.89837 -24.77316,1.17968 -24.77316,1.17968 0,0 -14.1561,-4.7187 -29.49186,-11.79674 -15.33577,-7.07805 -41.288614,-31.85121 -41.288614,-31.85121 l -55.44469,-66.06177 c 0,0 -2.35935,-8.25772 9.43739,-8.25772 -8.25772,-9.43739 -9.43739,-17.69511 -9.43739,-17.69511 l 4.7187,-8.25772 v -12.97642 c 0,0 -4.7187,-11.79675 11.79674,-4.7187 -10.61707,-5.89837 -7.07805,-18.87479 -9.43739,-35.39023 8.25772,24.77316 44.82762,54.26502 44.82762,54.26502 0,0 3.53902,5.89837 42.468284,22.41381 38.92925,16.51544 84.93655,12.97642 84.93655,12.97642 0,0 -1.17967,-1.17967 2.35935,-11.79674 3.53902,-10.61707 -12.97642,-8.25772 -16.51544,-30.67154 5.89837,-31.8512 -33.03088,-47.18697 -33.03088,-47.18697 0,0 8.25772,-5.89837 17.69511,-4.7187 9.4374,1.17968 -18.87479,-10.61707 -14.15609,-12.97642 4.7187,-2.35934 16.51544,4.7187 16.51544,4.7187 l -12.97642,-9.43739 c 0,0 1.17968,-2.35935 11.79675,-1.17968 10.61707,1.17968 -2.35935,-5.898367 -9.4374,-15.335757 10.61707,-4.7187 9.4374,4.71869 16.51544,4.71869 -1.17967,-9.43739 -14.15609,-22.41381 -14.15609,-22.41381 0,0 17.69512,4.7187 22.41381,11.79674 -2.35934,-10.61707 -14.15609,-33.030882 -14.15609,-33.030882 0,0 25.95284,5.898372 38.92926,18.874792 24.77316,24.77316 53.08534,53.085347 53.08534,53.085347 l 30.67154,56.62437 -21.23414,4.7187 9.43739,23.59348 z"/></svg>'
};

// ── Theme ──

function initTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (saved === 'dark' || (!saved && prefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  syncThemeIcon();
}

function toggleTheme() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', dark ? 'light' : 'dark');
  localStorage.setItem('theme', dark ? 'light' : 'dark');
  syncThemeIcon();
}

function syncThemeIcon() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  $('#icon-moon').style.display = dark ? 'none' : 'block';
  $('#icon-sun').style.display = dark ? 'block' : 'none';
}

// ── Tabs ──

function initTabs() {
  $$('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.tab').forEach(t => t.classList.remove('active'));
      $$('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      $(`#tab-${btn.dataset.tab}`).classList.add('active');
      if (btn.dataset.tab === 'queue') refreshQueue();
    });
  });
}

// ── Search ──

let searchType = 'track';
let currentSearchResults = [];

function initSearch() {
  $$('.chip[data-search]').forEach(chip => {
    chip.addEventListener('click', () => {
      $$('.chip[data-search]').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      searchType = chip.dataset.search;
      // Auto-search if there's a query
      const q = $('#search-input').value.trim();
      if (q) doSearch();
    });
  });
}

async function doSearch() {
  const query = $('#search-input').value.trim();
  if (!query) return;

  const container = $('#results-container');
  const sortWrapper = $('#search-sort-container');
  container.innerHTML = '<div class="empty-state"><p>Searching...</p></div>';
  sortWrapper.style.display = 'none';
  currentSearchResults = [];

  try {
    const results = await api('/search', { type: searchType, query });
    if (!results.length) {
      container.innerHTML = '<div class="empty-state"><p>No results found</p></div>';
      return;
    }
    currentSearchResults = results;
    sortWrapper.style.display = 'flex';
    $('#search-sort').value = 'default';
    renderSearchResults();
  } catch {
    container.innerHTML = '<div class="empty-state"><p>Search failed</p></div>';
  }
}

function renderSearchResults() {
  const container = $('#results-container');
  container.innerHTML = '';

  const sortValue = $('#search-sort').value;
  let items = [...currentSearchResults];

  if (sortValue === 'year-desc') {
    items.sort((a, b) => {
      const ya = parseInt(a.year) || 0;
      const yb = parseInt(b.year) || 0;
      return yb - ya;
    });
  } else if (sortValue === 'year-asc') {
    items.sort((a, b) => {
      const ya = parseInt(a.year) || 9999;
      const yb = parseInt(b.year) || 9999;
      return ya - yb;
    });
  } else if (sortValue === 'alpha-asc') {
    items.sort((a, b) => {
      const ta = (a.title || a.album || '').toLowerCase();
      const tb = (b.title || b.album || '').toLowerCase();
      return ta.localeCompare(tb);
    });
  } else if (sortValue === 'alpha-desc') {
    items.sort((a, b) => {
      const ta = (a.title || a.album || '').toLowerCase();
      const tb = (b.title || b.album || '').toLowerCase();
      return tb.localeCompare(ta);
    });
  } else if (sortValue === 'artist-asc') {
    items.sort((a, b) => {
      const aa = (a.artist || '').toLowerCase();
      const ab = (b.artist || '').toLowerCase();
      return aa.localeCompare(ab);
    });
  }

  items.forEach(item => container.appendChild(buildResult(item)));
}

function buildResult(item) {
  const wrapper = document.createElement('div');
  wrapper.className = 'result-wrapper';
  wrapper.dataset.id = item.id;
  wrapper.dataset.type = item.id_type;
  if (item.album_id) {
    wrapper.dataset.albumId = item.album_id;
  }
  if (item.downloaded) {
    wrapper.classList.add('downloaded');
  }

  const div = document.createElement('div');
  div.className = 'result-item';

  const img = item.img_url
    ? `<img class="result-img" src="${item.img_url}" alt="" loading="lazy">`
    : '<div class="result-img-placeholder"></div>';

  const title = item.title || item.album;
  const badgeHtml = item.downloaded
    ? `<span class="downloaded-badge" title="Already Downloaded">${ICONS.check}</span>`
    : (item.in_queue ? `<span class="queued-badge" title="In Download Queue">${ICONS.clock}</span>` : '');

  div.innerHTML = `
    ${img}
    <div class="result-info">
      <div class="result-title">${esc(title)}</div>
      <div class="result-meta"></div>
    </div>
    ${badgeHtml}
    <div class="result-actions"></div>
  `;
  
  const metaContainer = div.querySelector('.result-meta');
  
  const artistSpan = document.createElement('span');
  artistSpan.className = 'artist-name';
  artistSpan.textContent = item.artist;
  metaContainer.appendChild(artistSpan);

  if (item.year) {
    const yearSpan = document.createElement('span');
    yearSpan.className = 'release-year';
    yearSpan.textContent = ` (${item.year})`;
    metaContainer.appendChild(yearSpan);
  }

  if (item.title) {
    metaContainer.appendChild(document.createTextNode(' · '));
    
    const albumLink = document.createElement('span');
    albumLink.className = 'album-link';
    albumLink.textContent = item.album;
    albumLink.title = 'View Album';
    albumLink.addEventListener('click', (e) => {
      e.stopPropagation();
      showAlbumModal(item.album_id, item.album, item.artist, item.img_url);
    });
    metaContainer.appendChild(albumLink);
  }
  
  const actionsContainer = div.querySelector('.result-actions');
  
  if (item.preview_url) {
    const playBtn = document.createElement('button');
    playBtn.className = 'action-btn';
    playBtn.title = 'Preview';
    playBtn.innerHTML = ICONS.play;
    playBtn.addEventListener('click', () => playPreview(item.preview_url, title, item.artist));
    actionsContainer.appendChild(playBtn);
  }

  if (item.id_type === 'album') {
    const expandBtn = document.createElement('button');
    expandBtn.className = 'action-btn toggle-album-btn';
    expandBtn.title = 'Expand tracks';
    expandBtn.innerHTML = ICONS.chevronDown;
    expandBtn.addEventListener('click', () => toggleAlbum(item.album_id, expandBtn));
    actionsContainer.appendChild(expandBtn);
  }

  const dlBtn = document.createElement('button');
  dlBtn.className = 'action-btn download-btn';
  dlBtn.title = 'Download';
  dlBtn.innerHTML = ICONS.download;
  dlBtn.addEventListener('click', () => dlItem(item.id, item.id_type, false, title, item.artist, item.img_url));
  actionsContainer.appendChild(dlBtn);

  if (item.id_type === 'album') {
    const zipBtn = document.createElement('button');
    zipBtn.className = 'action-btn';
    zipBtn.title = 'Download ZIP';
    zipBtn.innerHTML = ICONS.zip;
    zipBtn.addEventListener('click', () => dlItem(item.id, item.id_type, true, title, item.artist, item.img_url));
    actionsContainer.appendChild(zipBtn);
  }

  wrapper.appendChild(div);

  if (item.id_type === 'album') {
    const tracksDiv = document.createElement('div');
    tracksDiv.className = 'album-tracks';
    wrapper.appendChild(tracksDiv);
  }

  return wrapper;
}

async function toggleAlbum(albumId, btn) {
  const wrapper = btn.closest('.result-wrapper');
  const tracksDiv = wrapper.querySelector('.album-tracks');
  const isExpanded = wrapper.classList.toggle('expanded');
  
  if (isExpanded) {
    if (tracksDiv.children.length === 0) {
      tracksDiv.innerHTML = '<div class="tracks-loading">Loading tracks...</div>';
      try {
        const tracks = await api('/search', { type: 'album_track', query: String(albumId) });
        tracksDiv.innerHTML = '';
        if (!tracks.length) {
          tracksDiv.innerHTML = '<div class="tracks-empty">No tracks found</div>';
        } else {
          // Find parent cover art
          const parentImg = wrapper.querySelector('.result-img');
          const parentCoverUrl = parentImg ? parentImg.src : '';

          tracks.forEach((track, i) => {
            const trackIndex = (i + 1).toString().padStart(2, '0');
            const trackRow = document.createElement('div');
            trackRow.className = 'album-track-item';
            trackRow.dataset.id = track.id;
            trackRow.dataset.type = 'track';
            trackRow.dataset.albumId = albumId;
            
            const badgeHtml = track.downloaded
              ? `<span class="downloaded-badge" title="Already Downloaded">${ICONS.check}</span>`
              : (track.in_queue ? `<span class="queued-badge" title="In Download Queue">${ICONS.clock}</span>` : '');

            trackRow.innerHTML = `
              <span class="track-index">${trackIndex}</span>
              <div class="track-info">
                <div class="track-title">${esc(track.title)}</div>
              </div>
              ${badgeHtml}
              <div class="track-actions"></div>
            `;
            
            const trackActions = trackRow.querySelector('.track-actions');
            
            if (track.preview_url) {
              const playBtn = document.createElement('button');
              playBtn.className = 'action-btn';
              playBtn.title = 'Preview';
              playBtn.innerHTML = ICONS.play;
              playBtn.addEventListener('click', () => playPreview(track.preview_url, track.title, track.artist));
              trackActions.appendChild(playBtn);
            }
            
            const dlBtn = document.createElement('button');
            dlBtn.className = 'action-btn download-btn';
            dlBtn.title = 'Download';
            dlBtn.innerHTML = ICONS.download;
            dlBtn.addEventListener('click', () => dlItem(track.id, 'track', false, track.title, track.artist, track.img_url || parentCoverUrl));
            trackActions.appendChild(dlBtn);
            
            tracksDiv.appendChild(trackRow);
          });
        }
      } catch (e) {
        tracksDiv.innerHTML = '<div class="tracks-error">Failed to load tracks</div>';
      }
    }
  }
}

// ── Preview & Custom Player ──

function formatTime(secs) {
  if (isNaN(secs)) return '0:00';
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function playPreview(url, title, artist = 'Deezer Preview') {
  const bar = $('#preview-bar');
  const audio = $('#audio-preview');
  
  $('#preview-title').textContent = title || 'Preview';
  $('#preview-artist').textContent = artist || '';
  
  audio.src = url;
  bar.style.display = 'flex';
  audio.play();
}

function closePreview() {
  const audio = $('#audio-preview');
  audio.pause();
  audio.src = '';
  $('#preview-bar').style.display = 'none';
}

function togglePlayPreview() {
  const audio = $('#audio-preview');
  if (audio.paused) {
    audio.play();
  } else {
    audio.pause();
  }
}

function toggleMutePreview() {
  const audio = $('#audio-preview');
  audio.muted = !audio.muted;
  $('#preview-volume-icon').style.display = audio.muted ? 'none' : 'block';
  $('#preview-mute-icon').style.display = audio.muted ? 'block' : 'none';
}

function seekPreview(e) {
  const audio = $('#audio-preview');
  const slider = $('#preview-slider');
  const rect = slider.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  if (audio.duration) {
    audio.currentTime = pct * audio.duration;
  }
}

// ── Album Modal ──

async function showAlbumModal(albumId, albumTitle, artistName, fallbackImgUrl) {
  const modal = $('#album-modal');
  const modalTitle = $('#album-modal-title');
  const modalName = $('#album-modal-name');
  const modalArtist = $('#album-modal-artist');
  const modalImg = $('#album-modal-img');
  const modalTracks = $('#album-modal-tracks');
  
  modalTitle.textContent = 'Album Details';
  modalName.textContent = albumTitle;
  modalArtist.textContent = artistName;
  modalImg.src = fallbackImgUrl || '';
  modalTracks.innerHTML = '<div class="tracks-loading">Loading tracks...</div>';
  
  // Setup download buttons on the modal
  const dlBtn = $('#btn-album-modal-dl');
  const zipBtn = $('#btn-album-modal-zip');
  
  // Remove old listeners by cloning
  const newDlBtn = dlBtn.cloneNode(true);
  const newZipBtn = zipBtn.cloneNode(true);
  dlBtn.parentNode.replaceChild(newDlBtn, dlBtn);
  zipBtn.parentNode.replaceChild(newZipBtn, zipBtn);
  
  newDlBtn.addEventListener('click', () => {
    dlItem(String(albumId), 'album', false, albumTitle, artistName, fallbackImgUrl);
  });
  newZipBtn.addEventListener('click', () => {
    dlItem(String(albumId), 'album', true, albumTitle, artistName, fallbackImgUrl);
  });
  
  modal.classList.add('show');
  
  try {
    const tracks = await api('/search', { type: 'album_track', query: String(albumId) });
    modalTracks.innerHTML = '';
    if (!tracks.length) {
      modalTracks.innerHTML = '<div class="tracks-empty">No tracks found</div>';
    } else {
      if (tracks[0].img_url) {
        modalImg.src = tracks[0].img_url;
      }
      
      tracks.forEach((track, i) => {
        const trackIndex = (i + 1).toString().padStart(2, '0');
        const trackRow = document.createElement('div');
        trackRow.className = 'album-track-item';
        trackRow.dataset.id = track.id;
        trackRow.dataset.type = 'track';
        trackRow.dataset.albumId = albumId;
        
        const badgeHtml = track.downloaded
          ? `<span class="downloaded-badge" title="Already Downloaded">${ICONS.check}</span>`
          : (track.in_queue ? `<span class="queued-badge" title="In Download Queue">${ICONS.clock}</span>` : '');

        trackRow.innerHTML = `
          <span class="track-index">${trackIndex}</span>
          <div class="track-info">
            <div class="track-title">${esc(track.title)}</div>
          </div>
          ${badgeHtml}
          <div class="track-actions"></div>
        `;
        
        const trackActions = trackRow.querySelector('.track-actions');
        if (track.preview_url) {
          const playBtn = document.createElement('button');
          playBtn.className = 'action-btn';
          playBtn.title = 'Preview';
          playBtn.innerHTML = ICONS.play;
          playBtn.addEventListener('click', () => playPreview(track.preview_url, track.title, track.artist));
          trackActions.appendChild(playBtn);
        }
        
        const dlTrackBtn = document.createElement('button');
        dlTrackBtn.className = 'action-btn download-btn';
        dlTrackBtn.title = 'Download';
        dlTrackBtn.innerHTML = ICONS.download;
        dlTrackBtn.addEventListener('click', () => dlItem(track.id, 'track', false, track.title, track.artist, track.img_url || modalImg.src));
        trackActions.appendChild(dlTrackBtn);
        
        modalTracks.appendChild(trackRow);
      });
    }
  } catch (e) {
    modalTracks.innerHTML = '<div class="tracks-error">Failed to load tracks</div>';
  }
}

function closeAlbumModal() {
  $('#album-modal').classList.remove('show');
}

// ── Settings State ──
let appSettings = {
  output_dir: '',
  layout_mode: 'compact',
  auto_redirect_queue: false,
  item_size: 'standard'
};

function applyLayoutMode(mode) {
  if (mode === 'full') {
    document.body.setAttribute('data-layout', 'full');
  } else {
    document.body.removeAttribute('data-layout');
  }
}

function applyDensitySettings(size) {
  const container = $('#results-container');
  if (container) {
    container.setAttribute('data-density', size || 'standard');
  }
}

async function refreshQueueBadge() {
  try {
    const tasks = await api('/queue');
    const active = tasks.filter(t => t.state === 'active' || t.state === 'queued').length;
    const badge = $('#queue-badge');
    if (active > 0) {
      badge.textContent = active;
      badge.style.display = 'inline';
    } else {
      badge.style.display = 'none';
    }
  } catch (e) {}
}

// ── Realtime Status Sync ──

const localQueued = new Set();
const localQueuedAlbums = new Set();

function updateRealtimeStatuses(tasks = []) {
  const queuedIds = new Set(localQueued);
  const downloadedIds = new Set();
  const queuedAlbumIds = new Set(localQueuedAlbums);
  const downloadedAlbumIds = new Set();

  tasks.forEach(t => {
    if (t.music_id && t.music_type) {
      const key = `${t.music_id}:${t.music_type}`;
      if (t.state === 'queued' || t.state === 'active') {
        queuedIds.add(key);
        if (t.music_type === 'album') {
          queuedAlbumIds.add(t.music_id);
        }
        localQueued.delete(key);
        if (t.music_type === 'album') {
          localQueuedAlbums.delete(t.music_id);
        }
      } else if (t.state === 'done') {
        downloadedIds.add(key);
        if (t.music_type === 'album') {
          downloadedAlbumIds.add(t.music_id);
        }
        localQueued.delete(key);
        if (t.music_type === 'album') {
          localQueuedAlbums.delete(t.music_id);
        }
      }
    }
  });

  // Update search results
  document.querySelectorAll('.result-wrapper').forEach(wrapper => {
    const id = wrapper.dataset.id;
    const type = wrapper.dataset.type;
    if (!id || !type) return;

    const key = `${id}:${type}`;
    const resultItem = wrapper.querySelector('.result-item');
    if (!resultItem) return;

    let isDownloaded = wrapper.classList.contains('downloaded') || 
                       resultItem.querySelector('.downloaded-badge') !== null ||
                       downloadedIds.has(key);
    
    let isQueued = !isDownloaded && (
      queuedIds.has(key) || 
      (type === 'track' && wrapper.dataset.albumId && queuedAlbumIds.has(wrapper.dataset.albumId))
    );

    if (type === 'album' && downloadedAlbumIds.has(id)) {
      isDownloaded = true;
    }

    updateBadge(resultItem, '.result-actions', isDownloaded, isQueued);
    if (isDownloaded) {
      wrapper.classList.add('downloaded');
    }
  });

  // Update track rows (expanded results & modal)
  document.querySelectorAll('.album-track-item').forEach(trackRow => {
    const id = trackRow.dataset.id;
    const type = 'track';
    if (!id) return;

    const key = `${id}:${type}`;
    const albumId = trackRow.dataset.albumId;

    let isDownloaded = trackRow.querySelector('.downloaded-badge') !== null ||
                       downloadedIds.has(key) ||
                       (albumId && downloadedAlbumIds.has(albumId));

    let isQueued = !isDownloaded && (
      queuedIds.has(key) || 
      (albumId && queuedAlbumIds.has(albumId))
    );

    updateBadge(trackRow, '.track-actions', isDownloaded, isQueued);
  });
}

function updateBadge(container, actionsSelector, isDownloaded, isQueued) {
  const existingDownloaded = container.querySelector('.downloaded-badge');
  const existingQueued = container.querySelector('.queued-badge');
  
  if (existingDownloaded) existingDownloaded.remove();
  if (existingQueued) existingQueued.remove();

  const actions = container.querySelector(actionsSelector);
  if (!actions) return;

  if (isDownloaded) {
    const badge = document.createElement('span');
    badge.className = 'downloaded-badge';
    badge.title = 'Already Downloaded';
    badge.innerHTML = ICONS.check;
    actions.before(badge);
  } else if (isQueued) {
    const badge = document.createElement('span');
    badge.className = 'queued-badge';
    badge.title = 'In Download Queue';
    badge.innerHTML = ICONS.clock;
    actions.before(badge);
  }
}

// ── Download ──

async function dlItem(id, type, zip, title, artist, imgUrl) {
  const label = type === 'album' ? (zip ? 'Downloading album as ZIP...' : 'Downloading album...') : 'Downloading track...';
  toast(label);

  const key = `${id}:${type}`;
  localQueued.add(key);
  if (type === 'album') {
    localQueuedAlbums.add(id);
  }
  updateRealtimeStatuses();

  await api('/download', {
    type,
    music_id: id,
    create_zip: zip,
    title: title,
    artist: artist,
    img_url: imgUrl
  });
  refreshQueueBadge();
  if (appSettings.auto_redirect_queue) {
    showTab('queue');
  }
}

async function downloadYouTube() {
  const url = $('#yt-input').value.trim();
  if (!url) return;
  toast('Downloading via yt-dlp...');
  await api('/youtube', { url });
  refreshQueueBadge();
  if (appSettings.auto_redirect_queue) {
    showTab('queue');
  } else {
    $('#yt-input').value = '';
  }
}

function showTab(name) {
  $$('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === name);
  });
  $$('.tab-content').forEach(t => {
    t.classList.toggle('active', t.id === `tab-${name}`);
  });
  if (name === 'queue') refreshQueue();
}

// ── Playlists ──

async function dlDeezerPl(zip) {
  const url = $('#deezer-playlist-url').value.trim();
  if (!url) return;
  toast('Downloading Deezer playlist...');
  await api('/playlist/deezer', { playlist_url: url, create_zip: zip });
  refreshQueueBadge();
  if (appSettings.auto_redirect_queue) {
    showTab('queue');
  } else {
    $('#deezer-playlist-url').value = '';
  }
}

async function dlSpotifyPl(zip) {
  const name = $('#spotify-playlist-name').value.trim();
  const url = $('#spotify-playlist-url').value.trim();
  if (!url) return;
  toast('Downloading Spotify playlist...');
  await api('/playlist/spotify', { playlist_name: name || 'spotify', playlist_url: url, create_zip: zip });
  refreshQueueBadge();
  if (appSettings.auto_redirect_queue) {
    showTab('queue');
  } else {
    $('#spotify-playlist-name').value = '';
    $('#spotify-playlist-url').value = '';
  }
}

async function dlDeezerFav() {
  const uid = $('#deezer-fav-uid').value.trim();
  if (!uid) return;
  toast('Downloading favorites...');
  await api('/favorites', { user_id: uid });
  refreshQueueBadge();
  if (appSettings.auto_redirect_queue) {
    showTab('queue');
  } else {
    $('#deezer-fav-uid').value = '';
  }
}

// ── Queue ──

let _queueTimer = null;

async function refreshQueue() {
  try {
    const tasks = await api('/queue');
    updateRealtimeStatuses(tasks);
    const container = $('#queue-container');
    const badge = $('#queue-badge');

    // Update badge
    const active = tasks.filter(t => t.state === 'active' || t.state === 'queued').length;
    if (active > 0) {
      badge.textContent = active;
      badge.style.display = 'inline';
    } else {
      badge.style.display = 'none';
    }

    const hasCompleted = tasks.some(t => t.state === 'done' || t.state === 'failed');
    $('#queue-actions-bar').style.display = hasCompleted ? 'flex' : 'none';

    if (!tasks.length) {
      container.innerHTML = '<div class="empty-state"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg><p>No downloads yet</p></div>';
      return;
    }

    container.innerHTML = '';
    tasks.forEach(t => {
      const div = document.createElement('div');
      div.className = 'queue-item';

      let img = '';
      if (t.img_url) {
        img = `<img class="queue-img" src="${t.img_url}" alt="" loading="lazy">`;
      } else {
        let iconSvg = '';
        if (t.description.toLowerCase().includes('youtube')) {
          iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>';
        } else {
          iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>';
        }
        img = `<div class="queue-img-placeholder">${iconSvg}</div>`;
      }

      let progress = '';
      if (t.state === 'active') {
        let activeText = t.current_item ? `<div class="queue-active-text">${esc(t.current_item)}</div>` : '';
        let progressRow = '';
        if (t.progress_max > 0) {
          const pct = Math.round((t.progress / t.progress_max) * 100);
          progressRow = `
            <div class="queue-progress-row">
              <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
              <span class="queue-progress-pct">${pct}%</span>
            </div>
          `;
        } else {
          progressRow = `
            <div class="queue-progress-row">
              <div class="progress-bar indeterminate"><div class="progress-fill"></div></div>
            </div>
          `;
        }
        progress = `${progressRow}${activeText}`;
      } else if (t.state === 'queued') {
        progress = `<div class="queue-active-text">Waiting in queue...</div>`;
      }

      let error = t.state === 'failed' && t.error
        ? `<div class="queue-error">${esc(t.error)}</div>` : '';

      let retryBtn = '';
      if (t.state === 'failed') {
        retryBtn = `<button class="btn retry-btn">Retry</button>`;
      }

      let cleanDesc = t.description;
      let cleanMeta = t.artist ? t.artist : 'Active task';
      
      if (t.title) {
        cleanDesc = t.title;
        let type = 'Task';
        const dLower = t.description.toLowerCase();
        if (dLower.includes('album')) {
          type = 'Album';
        } else if (dLower.includes('track')) {
          type = 'Track';
        } else if (dLower.includes('playlist')) {
          type = 'Playlist';
        } else if (dLower.includes('favorites')) {
          type = 'Favorites';
        } else if (dLower.includes('youtube')) {
          type = 'YouTube Audio';
        }
        
        if (t.artist) {
          if (type === 'Playlist' || type === 'Favorites') {
            cleanMeta = `${type} · ${t.artist}`;
          } else {
            cleanMeta = `${type} by ${t.artist}`;
          }
        } else {
          cleanMeta = type;
        }
      }

      let sourceLogosHtml = '';
      if (t.source) {
        const sources = t.source.split(',').map(s => s.trim().toLowerCase());
        sources.forEach(src => {
          if (LOGOS[src]) {
            sourceLogosHtml += `<span class="queue-source-logo ${src}" title="Source: ${src.charAt(0).toUpperCase() + src.slice(1)}">${LOGOS[src]}</span>`;
          }
        });
      }
      if (sourceLogosHtml) {
        sourceLogosHtml = `<span class="queue-source-logos">${sourceLogosHtml}</span>`;
      }

      div.innerHTML = `
        ${img}
        <div class="queue-info">
          <div class="queue-desc">${esc(cleanDesc)}</div>
          <div class="queue-meta-row">
            <span class="queue-meta">${esc(cleanMeta)}</span>
            ${sourceLogosHtml}
          </div>
          ${progress}${error}${retryBtn}
        </div>
        <span class="pill pill-${t.state}">${t.state}</span>
      `;

      if (t.state === 'failed') {
        const rBtn = div.querySelector('.retry-btn');
        if (rBtn) {
          rBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            rBtn.disabled = true;
            rBtn.textContent = 'Retrying...';
            await api('/queue/retry', { task_id: t.id });
            refreshQueue();
          });
        }
      }

      container.appendChild(div);
    });

    // Keep polling if active
    if (active > 0) {
      clearTimeout(_queueTimer);
      _queueTimer = setTimeout(refreshQueue, 1500);
    }
  } catch (e) {
    console.error('Queue refresh error', e);
  }
}

// ── Settings ──

async function openSettings() {
  const data = await api('/settings');
  appSettings = data;
  $('#settings-output-dir').value = data.output_dir || '';
  $('#settings-layout-mode').value = data.layout_mode || 'compact';
  $('#settings-item-size').value = data.item_size || 'standard';
  $('#settings-auto-redirect').checked = data.auto_redirect_queue || false;
  $('#settings-download-lrc').checked = data.download_lrc !== false;
  $('#settings-soulseek-enabled').checked = data.soulseek_enabled || false;
  $('#settings-soulseek-user').value = data.soulseek_username || '';
  $('#settings-soulseek-pass').value = data.soulseek_password || '';
  $('#settings-sldl-command').value = data.sldl_command || 'sldl';
  $('#soulseek-settings-details').style.display = data.soulseek_enabled ? 'flex' : 'none';
  $('#settings-storage-free').textContent = data.free_space || 'Unknown';
  $('#settings-modal').classList.add('show');
}

function closeSettings() { $('#settings-modal').classList.remove('show'); }

async function saveSettings() {
  const dir = $('#settings-output-dir').value.trim();
  if (!dir) return;
  const layout = $('#settings-layout-mode').value;
  const itemSize = $('#settings-item-size').value;
  const autoRedirect = $('#settings-auto-redirect').checked;
  const downloadLrc = $('#settings-download-lrc').checked;
  const soulseekEnabled = $('#settings-soulseek-enabled').checked;
  const soulseekUser = $('#settings-soulseek-user').value.trim();
  const soulseekPass = $('#settings-soulseek-pass').value.trim();
  const sldlCommand = $('#settings-sldl-command').value.trim();

  await api('/settings', {
    output_dir: dir,
    layout_mode: layout,
    auto_redirect_queue: autoRedirect,
    item_size: itemSize,
    download_lrc: downloadLrc,
    soulseek_enabled: soulseekEnabled,
    soulseek_username: soulseekUser,
    soulseek_password: soulseekPass,
    sldl_command: sldlCommand
  });

  appSettings = {
    output_dir: dir,
    layout_mode: layout,
    auto_redirect_queue: autoRedirect,
    item_size: itemSize,
    download_lrc: downloadLrc,
    soulseek_enabled: soulseekEnabled,
    soulseek_username: soulseekUser,
    soulseek_password: soulseekPass,
    sldl_command: sldlCommand
  };

  applyLayoutMode(layout);
  applyDensitySettings(itemSize);
  toast('Settings saved');
  closeSettings();
}

// ── Keyboard ──

function initKeys() {
  document.addEventListener('keydown', e => {
    if (e.target.id === 'search-input' && e.key === 'Enter') {
      e.preventDefault();
      doSearch();
    }
    if (e.target.id === 'yt-input' && e.key === 'Enter') {
      e.preventDefault();
      downloadYouTube();
    }
    if (e.key === 'k' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      $('#search-input').focus();
      $('#search-input').select();
      showTab('search');
    }
    if (e.key === 'Escape') {
      closeSettings();
      closeAlbumModal();
    }
  });
}

// ── Boot ──

async function checkDeezerHealth() {
  const badge = $('#deezer-health-badge');
  if (!badge) return;

  try {
    const health = await api('/health');
    if (health.status === 'ok') {
      badge.className = 'health-badge ok';
      badge.textContent = 'Deezer: Connected';
      badge.title = `Logged in as: ${health.username || 'unknown'}\nPremium Account: ${health.premium ? 'Yes' : 'No'}`;
    } else if (health.status === 'invalid') {
      badge.className = 'health-badge invalid';
      badge.textContent = 'Deezer: Expired';
      badge.title = health.message || 'ARL cookie is expired or invalid.';
    } else {
      badge.className = 'health-badge error';
      badge.textContent = 'Deezer: Error';
      badge.title = health.message || 'Unknown error occurred.';
    }
  } catch (e) {
    badge.className = 'health-badge error';
    badge.textContent = 'Deezer: Offline';
    badge.title = 'Failed to connect to local backend service.';
  }
}

async function loadSettingsOnBoot() {
  try {
    const data = await api('/settings');
    appSettings = data;
    applyLayoutMode(appSettings.layout_mode);
    applyDensitySettings(appSettings.item_size);
    refreshQueueBadge();
  } catch (e) {
    console.error("Failed to load settings on boot", e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initTabs();
  initSearch();
  initKeys();
  loadSettingsOnBoot();
  checkDeezerHealth();
  $('#search-sort').onchange = renderSearchResults;

  $('#btn-theme').onclick = toggleTheme;
  $('#btn-settings').onclick = openSettings;
  $('#btn-close-settings').onclick = closeSettings;
  $('#btn-save-settings').onclick = saveSettings;
  $('#settings-soulseek-enabled').onchange = () => {
    $('#soulseek-settings-details').style.display = $('#settings-soulseek-enabled').checked ? 'flex' : 'none';
  };
  $('#btn-close-preview').onclick = closePreview;
  $('#btn-preview-play').onclick = togglePlayPreview;
  $('#btn-preview-mute').onclick = toggleMutePreview;
  $('#preview-slider').onclick = seekPreview;
  $('#btn-close-album-modal').onclick = closeAlbumModal;
  $('#btn-yt-download').onclick = downloadYouTube;
  $('#btn-deezer-pl').onclick = () => dlDeezerPl(false);
  $('#btn-deezer-pl-zip').onclick = () => dlDeezerPl(true);
  $('#btn-spotify-pl').onclick = () => dlSpotifyPl(false);
  $('#btn-spotify-pl-zip').onclick = () => dlSpotifyPl(true);
  $('#btn-deezer-fav').onclick = dlDeezerFav;
  $('#btn-clear-queue').onclick = async () => {
    await api('/queue/clear', {});
    refreshQueue();
  };

  // Custom audio player sync events
  const audio = $('#audio-preview');
  
  audio.addEventListener('play', () => {
    $('#preview-play-icon').style.display = 'none';
    $('#preview-pause-icon').style.display = 'block';
  });
  
  audio.addEventListener('pause', () => {
    $('#preview-play-icon').style.display = 'block';
    $('#preview-pause-icon').style.display = 'none';
  });
  
  audio.addEventListener('timeupdate', () => {
    const cur = audio.currentTime;
    const dur = audio.duration || 0;
    $('#preview-time-current').textContent = formatTime(cur);
    if (dur > 0) {
      const pct = (cur / dur) * 100;
      $('#preview-slider-fill').style.width = pct + '%';
    }
  });
  
  audio.addEventListener('loadedmetadata', () => {
    $('#preview-time-total').textContent = formatTime(audio.duration);
  });
  
  audio.addEventListener('ended', () => {
    $('#preview-play-icon').style.display = 'block';
    $('#preview-pause-icon').style.display = 'none';
    $('#preview-slider-fill').style.width = '0%';
    $('#preview-time-current').textContent = '0:00';
  });

  // Background queue poll for badge
  setInterval(() => {
    api('/queue').then(tasks => {
      const active = tasks.filter(t => t.state === 'active' || t.state === 'queued').length;
      const badge = $('#queue-badge');
      if (active > 0) {
        badge.textContent = active;
        badge.style.display = 'inline';
      } else {
        badge.style.display = 'none';
      }
      updateRealtimeStatuses(tasks);
    }).catch(() => {});
  }, 5000);

  // Periodic ARL health checks
  setInterval(checkDeezerHealth, 60000);
});
