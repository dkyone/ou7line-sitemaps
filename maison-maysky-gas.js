// ═══════════════════════════════════════════════════════════════════════════
//  Maison Maysky – PDF + Translation + Image Sync + Source Scraper
// ═══════════════════════════════════════════════════════════════════════════

// ─── Config ──────────────────────────────────────────────────────────────────

var FOLDER_ID          = '1RlFU8Ka3BgXiDp-3KrovFACgC74dZivM';
var AIRTABLE_BASE      = 'appdnkhejvx5bE6IV';
var AIRTABLE_TABLE     = 'tblT6NLcBsuveFrV3';
var AIRTABLE_TOKEN     = '/* REDACTED — set in Script Properties or paste here */';
var CLOUDINARY_CLOUD   = 'dmnly140t';
var CLOUDINARY_PRESET  = 'maison-maysky';
var FLEXI_TOKEN        = '/* REDACTED — set in Script Properties or paste here */';

var FLEXI_TEMPLATES = { en: '6a1947aa1e0cf45b6d06c0a7', fr: '6a22b4855e6258160cf80276', ru: '6a22b8005e6258160cf80279' };
var PDF_FIELDS      = { en: 'fldAuf1MJRB8CntSk', fr: 'fld7z659DUwj8oQkk', ru: 'fld7B6V3Q8Ea0RFMp' };

// ─── Field IDs ────────────────────────────────────────────────────────────────

var FIELD_PDF_TRIGGER  = 'fldSX4qaGci4XrFRa';
var FIELD_PDF_FOLDER   = 'fld9jNb2S7dBzkPTm';
var FIELD_PDF_LOCK     = 'fldN6rmI6wfAPFKvh';
var FIELD_ID           = 'fldCGLy2FpBiVSbDt';
var FIELD_VILLA_NAME   = 'fld8kvYIJu1XLDOfe';
var FIELD_GALLERY_SRC  = 'fldIyp4jUC2yLl3xe';
var FIELD_GALLERY_169  = 'fldYEzhea5HA5N4yq';
var FIELD_SOURCE       = 'fldrnOnR0jbDcncwI';
var FIELD_LOCATION     = 'fld21Q75vyHskUtxG';
var FIELD_BEDROOMS     = 'fldmr8w7aKpyRMyX2';
var FIELD_BATHROOMS    = 'fld6k2XXnydO5qOpt';
var FIELD_GUESTS       = 'fldQJKRKhUgf36YZo';
var FIELD_AREA         = 'fldsiESbIyz5hVgcU';
var FIELD_PRICE_LOW    = 'fldo5UfLPk8htsoOd';
var FIELD_PRICE_HIGH   = 'fldHKxHVaLld4pXNl';
var FIELD_EQUIPEMENTS  = 'fldn55oEbtBt01NGp';
var FIELD_BUILDING     = 'fldlbJKQbitC5DIn2';
var FIELD_SECURITY     = 'fldAc3LHEzVvoa0kT';
var FIELD_SPORT        = 'fldxC2CQn7hygAAFh';
var FIELD_EXTERIOR     = 'fld3Mv4VhaNRqbMiQ';
var FIELD_SERVICES     = 'fldFxoujcFAKssEo4';
var FIELD_VIEWS        = 'fldoc6lRHUqdsaGo1';
var FIELD_NOTES        = 'fld4tws4ZYzwQfAhU';

var TF_IDS = [
  { en: 'fld8eyQTsG9U0C7KY', fr: 'fldYnDtQ9e2iRJoJ8', ru: 'fld8oR0jCowthIpfo' },
  { en: 'fldgvegFiwxPxpL93', fr: 'fldtAyjek672TVcrB', ru: 'fld5cgenk5ZJ1eR62' }
];
var FF_IDS = [
  { en: 'fldetX7AlE0zwCJXp', fr: 'fldW0g6MsQ8oZogH0', ru: 'fldFGmPNW6shj1FZx' },
  { en: 'fld4ra4POQAeS29gv', fr: 'fldjcnSm4vvWtnqEL', ru: 'fldGcEjM1BHsf6BJj' },
  { en: 'fldV6b9opNqRIqNUg', fr: 'fldlRspFKbH9SBDl1', ru: 'fldrTYi1hzYXLJQvn' },
  { en: 'fldIqDvONPkqbOFiF', fr: 'fldkoSOtYZh3TDy0i', ru: 'fldgehNtPyOpNvJXh' },
  { en: 'fldwkycgFvqJVJFb6', fr: 'fldIdapMYx8nYyuTb', ru: 'fldKKbFsR72YKIlaD' }
];

var TIME_LIMIT = 5 * 60 * 1000;

// ─── Airtable helpers ────────────────────────────────────────────────────────

function airtableHeaders() {
  return { Authorization: 'Bearer ' + AIRTABLE_TOKEN, 'Content-Type': 'application/json' };
}

function fetchRecord(recordId) {
  var url = 'https://api.airtable.com/v0/' + AIRTABLE_BASE + '/' + AIRTABLE_TABLE + '/' + recordId
          + '?returnFieldsByFieldId=true';
  var res = UrlFetchApp.fetch(url, { headers: airtableHeaders(), muteHttpExceptions: true });
  return JSON.parse(res.getContentText());
}

function fetchAllRecords(fieldIds) {
  var records = [], offset = null;
  do {
    var qs = 'returnFieldsByFieldId=true';
    qs += '&' + fieldIds.map(function(id) { return 'fields[]=' + encodeURIComponent(id); }).join('&');
    if (offset) qs += '&offset=' + encodeURIComponent(offset);
    var url = 'https://api.airtable.com/v0/' + AIRTABLE_BASE + '/' + AIRTABLE_TABLE + '?' + qs;
    var res = UrlFetchApp.fetch(url, { headers: airtableHeaders(), muteHttpExceptions: true });
    var data = JSON.parse(res.getContentText());
    if (data.records) records = records.concat(data.records);
    offset = data.offset || null;
  } while (offset);
  return records;
}

function patchRecord(recordId, fields) {
  var url = 'https://api.airtable.com/v0/' + AIRTABLE_BASE + '/' + AIRTABLE_TABLE + '/' + recordId;
  var res = UrlFetchApp.fetch(url, {
    method: 'PATCH',
    headers: airtableHeaders(),
    payload: JSON.stringify({ fields: fields }),
    muteHttpExceptions: true
  });
  return JSON.parse(res.getContentText());
}

// ─── FlexiPage ───────────────────────────────────────────────────────────────

function triggerFlexiPdf(lang, recordId) {
  var res = UrlFetchApp.fetch('https://api.flexipage.app/merge', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + FLEXI_TOKEN, 'Content-Type': 'application/json' },
    payload: JSON.stringify({
      templateId: FLEXI_TEMPLATES[lang], recordId: recordId,
      tableId: AIRTABLE_TABLE, airtableToken: AIRTABLE_TOKEN, baseId: AIRTABLE_BASE,
      deliveryOption: { baseId: AIRTABLE_BASE, recordId: recordId, writeFieldId: PDF_FIELDS[lang] }
    }),
    muteHttpExceptions: true
  });
  Logger.log('FlexiPage ' + lang + ': ' + res.getResponseCode() + ' ' + res.getContentText().substring(0, 200));
}

function pollForPdfs(recordId, timeoutMs) {
  var deadline = Date.now() + timeoutMs;
  var prevCounts = null;
  while (Date.now() < deadline) {
    Utilities.sleep(15000);
    var rec = fetchRecord(recordId);
    var f = rec.fields || {};
    var en = f[PDF_FIELDS.en], fr = f[PDF_FIELDS.fr], ru = f[PDF_FIELDS.ru];
    var counts = [en ? en.length : 0, fr ? fr.length : 0, ru ? ru.length : 0];
    Logger.log('Poll: EN=' + counts[0] + ' FR=' + counts[1] + ' RU=' + counts[2]);
    if (counts[0] >= 1 && counts[1] >= 1 && counts[2] >= 1) {
      if (prevCounts && counts[0] === prevCounts[0] && counts[1] === prevCounts[1] && counts[2] === prevCounts[2]) {
        Logger.log('Counts stable.');
        return { en: en, fr: fr, ru: ru };
      }
    }
    prevCounts = counts;
  }
  var rec = fetchRecord(recordId);
  var f = rec.fields || {};
  return { en: f[PDF_FIELDS.en], fr: f[PDF_FIELDS.fr], ru: f[PDF_FIELDS.ru] };
}

// ─── PDF pipeline ────────────────────────────────────────────────────────────

function runForRecord(recordId) {
  var startTime = Date.now();
  var rec = fetchRecord(recordId);
  if (!rec || !rec.fields) { Logger.log('Record not found: ' + recordId); return; }
  var f = rec.fields;
  var villaName = f[FIELD_VILLA_NAME] || f[FIELD_ID] || recordId;
  Logger.log('▶ PDF pipeline: ' + villaName);
  var clear = {};
  clear[PDF_FIELDS.en] = []; clear[PDF_FIELDS.fr] = []; clear[PDF_FIELDS.ru] = [];
  patchRecord(recordId, clear);
  ['en', 'fr', 'ru'].forEach(function(lang) { triggerFlexiPdf(lang, recordId); });
  var pdfs = pollForPdfs(recordId, 180000);
  var bytes = {};
  ['en', 'fr', 'ru'].forEach(function(lang) {
    var atts = pdfs[lang];
    if (atts && atts.length) bytes[lang] = UrlFetchApp.fetch(atts[atts.length - 1].url).getContent();
  });
  var parent = DriveApp.getFolderById(FOLDER_ID);
  var it = parent.getFoldersByName(villaName);
  var folder = it.hasNext() ? it.next() : parent.createFolder(villaName);
  ['en', 'fr', 'ru'].forEach(function(lang) {
    if (!bytes[lang]) return;
    var name = villaName + '_' + lang.toUpperCase() + '.pdf';
    var old = folder.getFilesByName(name);
    while (old.hasNext()) old.next().setTrashed(true);
    folder.createFile(Utilities.newBlob(bytes[lang], 'application/pdf', name));
  });
  var updates = {};
  ['en', 'fr', 'ru'].forEach(function(lang) {
    var atts = pdfs[lang];
    if (atts && atts.length) updates[PDF_FIELDS[lang]] = [{ id: atts[atts.length - 1].id }];
  });
  updates[FIELD_PDF_FOLDER]  = 'https://drive.google.com/drive/folders/' + folder.getId();
  updates[FIELD_PDF_TRIGGER] = false;
  patchRecord(recordId, updates);
  Logger.log('✅ PDF done in ' + Math.round((Date.now() - startTime) / 1000) + 's: ' + villaName);
}

function processCheckboxPDF() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) { Logger.log('Another instance running'); return; }
  try {
    var records = fetchAllRecords([FIELD_PDF_TRIGGER, FIELD_PDF_LOCK]);
    var pending = records.filter(function(r) {
      return r.fields && r.fields[FIELD_PDF_TRIGGER] && !r.fields[FIELD_PDF_LOCK];
    });
    if (!pending.length) return;
    var r = pending[0];
    patchRecord(r.id, { [FIELD_PDF_LOCK]: 'processing' });
    try { runForRecord(r.id); }
    catch(e) { Logger.log('Error: ' + e); patchRecord(r.id, { [FIELD_PDF_TRIGGER]: false, [FIELD_PDF_LOCK]: '' }); }
    finally { patchRecord(r.id, { [FIELD_PDF_LOCK]: '' }); }
  } finally { try { lock.releaseLock(); } catch(e) {} }
}

function cleanupStuckLocks() {
  var records = fetchAllRecords([FIELD_PDF_LOCK]);
  var cleaned = 0;
  records.forEach(function(r) {
    if (r.fields && r.fields[FIELD_PDF_LOCK]) { patchRecord(r.id, { [FIELD_PDF_LOCK]: '' }); cleaned++; }
  });
  Logger.log('cleanupStuckLocks: ' + cleaned);
}

// ─── Переводы ─────────────────────────────────────────────────────────────────

function translateAll() {
  var allFieldIds = [];
  TF_IDS.forEach(function(g) { allFieldIds.push(g.en, g.fr, g.ru); });
  FF_IDS.forEach(function(g) { allFieldIds.push(g.en, g.fr, g.ru); });
  var records = fetchAllRecords(allFieldIds);
  var updated = 0;
  records.forEach(function(r) {
    if (!r.fields) return;
    var patch = {};
    translateTextFields(r.fields, patch);
    translateFormattedFields(r.fields, patch);
    if (Object.keys(patch).length) { patchRecord(r.id, patch); updated++; }
  });
  Logger.log('translateAll: ' + updated);
}

function translateTextFields(fields, patch) {
  TF_IDS.forEach(function(g) {
    var src = fields[g.fr] || fields[g.en];
    if (!src) return;
    var srcLang = fields[g.fr] ? 'fr' : 'en';
    if (!fields[g.en] && fields[g.fr]) { try { patch[g.en] = LanguageApp.translate(src, 'fr', 'en'); } catch(e) {} }
    if (!fields[g.fr] && fields[g.en]) { try { patch[g.fr] = LanguageApp.translate(fields[g.en], 'en', 'fr'); } catch(e) {} }
    if (!fields[g.ru]) { try { patch[g.ru] = LanguageApp.translate(src, srcLang, 'ru'); } catch(e) {} }
  });
}

function translateFormattedFields(fields, patch) {
  FF_IDS.forEach(function(g) {
    var src = fields[g.en];
    if (!src) return;
    if (!fields[g.fr]) { try { patch[g.fr] = LanguageApp.translate(src, 'en', 'fr'); } catch(e) {} }
    if (!fields[g.ru]) { try { patch[g.ru] = LanguageApp.translate(src, 'en', 'ru'); } catch(e) {} }
  });
}

// ─── Image Sync (Cloudinary 16:9) ────────────────────────────────────────────

function processNewImages() {
  var startTime = Date.now();
  var records   = fetchAllRecords([FIELD_GALLERY_SRC, FIELD_GALLERY_169, FIELD_VILLA_NAME]);
  var synced    = 0;
  for (var i = 0; i < records.length; i++) {
    if (Date.now() - startTime > TIME_LIMIT) { Logger.log('Time limit reached.'); break; }
    var r = records[i];
    if (!r.fields) continue;
    var src = r.fields[FIELD_GALLERY_SRC];
    if (!src || !src.length) continue;
    var dst    = r.fields[FIELD_GALLERY_169] || [];
    var srcIds = src.map(function(img) { return img.id; });

    // Step 1 — Remove stale (items whose filename doesn't match any source att-ID)
    var validDst = dst.filter(function(d) {
      var fname = d.filename || '';
      return srcIds.some(function(id) { return fname.indexOf(id) !== -1; });
    });

    // Step 2 — Deduplicate: keep only first occurrence per srcId
    var seen = {};
    var dedupedDst = validDst.filter(function(d) {
      var fname   = d.filename || '';
      var matchId = srcIds.filter(function(id) { return fname.indexOf(id) !== -1; })[0];
      if (!matchId || seen[matchId]) return false;
      seen[matchId] = true;
      return true;
    });

    // Step 3 — Find missing uploads
    var dstText = dedupedDst.map(function(d) { return d.filename || ''; }).join(' ');
    var missing = src.filter(function(img) { return dstText.indexOf(img.id) === -1; });

    if (!missing.length && dedupedDst.length === dst.length) continue;

    var name       = r.fields[FIELD_VILLA_NAME] || r.id;
    var staleCount = dst.length - validDst.length;
    var dupCount   = validDst.length - dedupedDst.length;
    if (staleCount > 0) Logger.log(name + ': removing ' + staleCount + ' stale');
    if (dupCount   > 0) Logger.log(name + ': removing ' + dupCount   + ' duplicate');
    if (missing.length) Logger.log(name + ': adding '   + missing.length);

    var added = missing.map(function(img) {
      if (!img.url) return null;
      try   { return { url: uploadToCloudinary(img.url, img.id) }; }
      catch (e) { Logger.log('Cloudinary error ' + img.id + ': ' + e); return null; }
    }).filter(Boolean);

    var patch = {};
    patch[FIELD_GALLERY_169] = dedupedDst.map(function(d) { return { id: d.id }; }).concat(added);
    patchRecord(r.id, patch);
    synced++;
  }
  Logger.log('processNewImages: synced ' + synced);
}

function uploadToCloudinary(imageUrl, attachmentId) {
  var uploadUrl = 'https://api.cloudinary.com/v1_1/' + CLOUDINARY_CLOUD + '/image/upload';
  var payload = { file: imageUrl, upload_preset: CLOUDINARY_PRESET };
  if (attachmentId) payload.public_id = attachmentId;
  var res = UrlFetchApp.fetch(uploadUrl, { method: 'POST', payload: payload, muteHttpExceptions: true });
  var data = JSON.parse(res.getContentText());
  if (!data.secure_url) throw new Error('Cloudinary failed: ' + res.getContentText());
  return data.secure_url;
}

// ═══════════════════════════════════════════════════════════════════════════
//  SOURCE SCRAPER — HTML helpers
// ═══════════════════════════════════════════════════════════════════════════

function fetchHtml(url) {
  try {
    var res = UrlFetchApp.fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'Referer': 'https://www.google.com/'
      },
      muteHttpExceptions: true
    });
    if (res.getResponseCode() !== 200) { Logger.log('fetchHtml ' + res.getResponseCode() + ': ' + url); return null; }
    return res.getContentText();
  } catch(e) { Logger.log('fetchHtml error: ' + e); return null; }
}

function getMeta(html, property) {
  var patterns = [
    new RegExp('<meta[^>]+property=["\']' + property + '["\'][^>]+content=["\']([^"\']+)["\']', 'i'),
    new RegExp('<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']' + property + '["\']', 'i'),
    new RegExp('<meta[^>]+name=["\']' + property + '["\'][^>]+content=["\']([^"\']+)["\']', 'i')
  ];
  for (var i = 0; i < patterns.length; i++) {
    var m = html.match(patterns[i]);
    if (m) return decodeHtmlEntities(m[1].trim());
  }
  return null;
}

function getJsonLd(html) {
  var m = html.match(/<script[^>]+type=["\']application\/ld\+json["\'][^>]*>([\s\S]*?)<\/script>/i);
  if (!m) return null;
  try { return JSON.parse(m[1]); } catch(e) { return null; }
}

function decodeHtmlEntities(str) {
  if (!str) return str;
  return str.replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>')
            .replace(/&quot;/g,'"').replace(/&#039;/g,"'").replace(/&nbsp;/g,' ');
}

function extractNumber(str) {
  if (!str) return null;
  var m = str.replace(/\s/g,'').match(/[\d,\.]+/);
  if (!m) return null;
  return parseFloat(m[0].replace(/,/g,''));
}

function extractImages(html, baseUrl) {
  var urls = [], seen = {};
  var ogImg = getMeta(html, 'og:image');
  if (ogImg && !seen[ogImg]) { urls.push(ogImg); seen[ogImg] = true; }
  var imgRe = /<img[^>]+src=["\']([^"\']+)["\'][^>]*>/gi;
  var m;
  while ((m = imgRe.exec(html)) !== null) {
    var src = m[1];
    if (src.indexOf('data:') === 0) continue;
    if (src.indexOf('//') === 0) src = 'https:' + src;
    if (src.indexOf('/') === 0 && baseUrl) src = baseUrl + src;
    if (!seen[src] && isImageUrl(src)) { urls.push(src); seen[src] = true; }
  }
  return urls;
}

function isImageUrl(url) {
  return /\.(jpg|jpeg|png|webp|gif)(\?|$)/i.test(url);
}

// ═══════════════════════════════════════════════════════════════════════════
//  AMENITY KEYWORD MAPPING
// ═══════════════════════════════════════════════════════════════════════════

var AMENITY_KEYWORDS = {
  equipements: [
    ['air conditioning','Air conditioning'], ['climatisation','Air conditioning'], [' ac ','Air conditioning'],
    ['heating','Heating'], ['chauffage','Heating'],
    ['fireplace','Fireplace'], ['cheminée','Fireplace'],
    ['wi-fi','Internet / Wi-Fi'], ['wifi','Internet / Wi-Fi'], ['internet','Internet / Wi-Fi'],
    ['jacuzzi','Jacuzzi'],
    ['spa bath','Spa bath'], ['bain spa','Spa bath'],
    ['sauna','Sauna'],
    ['hammam','Hammam'],
    ['furnished','Furnished'], ['meublé','Furnished'],
    ['smart house','Smart house'], ['domotique','Smart house'], ['domotics','Smart house'], ['home automation','Smart house'],
    ['washing machine','Washing machine'], ['lave-linge','Washing machine'], ['washer','Washing machine'],
    ['dryer','Dryer'], ['sèche-linge','Dryer'],
    ['king size','King size bed'],
    ['electric vehicle','Electric vehicle charging']
  ],
  building: [
    ['elevator','Elevator'], ['lift','Elevator'], ['ascenseur','Elevator'],
    ['wine cellar','Wine cellar'], ['cave à vin','Wine cellar'],
    ['home cinema','Home cinema'], ['private cinema','Home cinema'], ['cinéma','Home cinema'], ['cinema room','Home cinema'],
    ['pool house','Pool house'],
    ['fiber','Fiber optics'], ['fibre','Fiber optics'], ['fiber optic','Fiber optics']
  ],
  security: [
    ['alarm','Alarm'], ['alarme','Alarm'],
    ['guard','Guard'], ['gardien','Guard'], ['security guard','Security guard'],
    ['electric gate','Electric gates'], ['portail électrique','Electric gates'],
    ['video surveillance','Video surveillance'], ['vidéosurveillance','Video surveillance'], ['videosurveillance','Video surveillance'],
    ['digicode','Digicode'],
    ['interphone','Interphone'], ['intercom','Interphone'], ['videophone','Interphone'],
    ['gated estate','Gated estate'], ['domaine privé','Gated estate'], ['domaine fermé','Gated estate'],
    ['armored','Armored door'], ['armoured','Armored door'],
    ['safe','Safe']
  ],
  sport: [
    ['gym','Gym'], ['fitness','Gym'], ['salle de sport','Gym'], ['sport room','Gym'],
    ['tennis','Tennis'],
    [' spa','Spa'], ['spa ','Spa'],
    ['massage room','Massage room'], ['salle de massage','Massage room'],
    ['golf','Golf'],
    ['ping-pong','Ping-pong'], ['table tennis','Ping-pong'],
    ['helipad','Helipad'], ['héliport','Helipad'], ['heliport','Helipad'],
    ['playground','Playground'],
    ['steam room','Steam room'],
    ['lawn bowls','Lawn bowls'], ['pétanque','Pétanque court'], ['petanque','Pétanque court']
  ],
  exterior: [
    ['infinity pool','Infinity pool'], ['piscine à débordement','Infinity pool'], ['pool à débordement','Infinity pool'],
    ['heated pool','Heated pool'], ['piscine chauffée','Heated pool'],
    ['swimming pool','Pool'], ['piscine','Pool'], [' pool','Pool'],
    ['garden','Garden'], ['jardin','Garden'],
    ['rooftop terrace','Rooftop terrace'], ['rooftop','Rooftop terrace'],
    ['terrace','Terrace'], ['terrasse','Terrace'],
    ['barbecue','Barbecue'], ['barbeque','Barbecue'], ['bbq','Barbecue'],
    ['patio','Patio'],
    ['direct sea access','Direct sea access'], ['accès mer','Direct sea access'], ['sea access','Direct sea access'],
    ['fountain','Fountain'], ['fontaine','Fountain'],
    ['irrigation','Irrigation']
  ]
};

function mapAmenities(text) {
  var lower = (' ' + text + ' ').toLowerCase();
  var result = { equipements: [], building: [], security: [], sport: [], exterior: [] };
  Object.keys(AMENITY_KEYWORDS).forEach(function(cat) {
    var seen = {};
    AMENITY_KEYWORDS[cat].forEach(function(pair) {
      if (lower.indexOf(pair[0].toLowerCase()) !== -1 && !seen[pair[1]]) {
        result[cat].push(pair[1]);
        seen[pair[1]] = true;
      }
    });
  });
  return result;
}

// ═══════════════════════════════════════════════════════════════════════════
//  LOCATION MATCHING
// ═══════════════════════════════════════════════════════════════════════════

var LOCATIONS = [
  'Menton','Roquebrune-Cap-Martin','Monaco','Monte-Carlo','Cap-d\'Ail',
  'Èze-sur-Mer','Beaulieu-sur-Mer','Saint-Jean-Cap-Ferrat','Villefranche-sur-Mer',
  'Nice','Saint-Laurent-du-Var','Cagnes-sur-Mer','Villeneuve-Loubet',
  'Antibes','Juan-les-Pins','Cap d\'Antibes','Golfe-Juan','Vallauris',
  'Cannes','Mougins','Biot','Vence','Saint-Paul-de-Vence','Grasse',
  'Tourrettes-sur-Loup','Saint-Tropez','Ramatuelle','Èze','Théoule-sur-Mer'
];

var LOCATION_ALIASES = {
  'st tropez': 'Saint-Tropez', 'st-tropez': 'Saint-Tropez',
  'cap ferrat': 'Saint-Jean-Cap-Ferrat', 'cap-ferrat': 'Saint-Jean-Cap-Ferrat',
  'cap antibes': 'Cap d\'Antibes', 'cap d\'antibes': 'Cap d\'Antibes',
  'monte carlo': 'Monaco', 'monaco': 'Monaco',
  'juan les pins': 'Juan-les-Pins',
  'golfe juan': 'Golfe-Juan',
  'saint paul': 'Saint-Paul-de-Vence',
  'st jean': 'Saint-Jean-Cap-Ferrat',
  'theoulé': 'Théoule-sur-Mer', 'theoule': 'Théoule-sur-Mer',
  'eze': 'Èze'
};

function matchLocation(text) {
  if (!text) return null;
  var lower = text.toLowerCase();
  for (var alias in LOCATION_ALIASES) {
    if (lower.indexOf(alias) !== -1) return LOCATION_ALIASES[alias];
  }
  for (var i = 0; i < LOCATIONS.length; i++) {
    if (lower.indexOf(LOCATIONS[i].toLowerCase()) !== -1) return LOCATIONS[i];
  }
  return null;
}

// ═══════════════════════════════════════════════════════════════════════════
//  PARSERS — 8 dedicated + 1 generic
// ═══════════════════════════════════════════════════════════════════════════

// ─── 1. Excellence Riviera ───────────────────────────────────────────────────
function parseExcellenceRiviera(html, url) {
  var d = {};
  d.title       = getMeta(html, 'og:title') || getMeta(html, 'title');
  d.description = getMeta(html, 'og:description');
  d.location    = matchLocation(url + ' ' + (d.title || ''));
  var guestsM = html.match(/(\d+)\s*(?:guests?|personnes?)/i);
  var bedsM   = html.match(/(\d+)\s*(?:bedroom|chambre)/i);
  var bathsM  = html.match(/(\d+)\s*(?:bathroom|salle de bain)/i);
  var areaM   = html.match(/(\d+)\s*m[²2]/i);
  var priceLM = html.match(/€\s*([\d\s,]+)\s*\/\s*week/i);
  var priceHM = html.match(/€\s*([\d\s,]+)\s*[^€]*high/i);
  if (guestsM) d.guests    = parseInt(guestsM[1]);
  if (bedsM)   d.bedrooms  = parseInt(bedsM[1]);
  if (bathsM)  d.bathrooms = parseInt(bathsM[1]);
  if (areaM)   d.area      = parseInt(areaM[1]);
  if (priceLM) d.priceLow  = extractNumber(priceLM[1]);
  if (priceHM) d.priceHigh = extractNumber(priceHM[1]);
  var photoRe = /https?:\/\/excellenceriviera\.com\/wp-content\/uploads\/[^\s"'<>]+\.(?:jpg|jpeg|png|webp)/gi;
  var photos = [], seen = {}, m;
  while ((m = photoRe.exec(html)) !== null) {
    if (!seen[m[0]]) { photos.push(m[0]); seen[m[0]] = true; }
  }
  d.photos = photos;
  d.amenityText = html;
  return d;
}

// ─── 2. Le Collectionist ─────────────────────────────────────────────────────
function parseLecollectionist(html, url) {
  var d = {};
  d.title       = getMeta(html, 'og:title');
  d.description = getMeta(html, 'og:description');
  d.location    = matchLocation(url + ' ' + (d.title || ''));
  var guestsM = html.match(/(\d+)\s*(?:guests?|personnes?)/i);
  var bedsM   = html.match(/(\d+)\s*(?:bed(?:room)?s?|chambre)/i);
  var bathsM  = html.match(/(\d+)\s*(?:bath(?:room)?s?|salle)/i);
  var areaM   = html.match(/(\d+)\s*(?:sqm|m[²2])/i);
  var priceM  = html.match(/€\s*([\d\s,]+)\s*(?:per\s*(?:7\s*nights?|week)|\/\s*week)/i);
  if (guestsM) d.guests    = parseInt(guestsM[1]);
  if (bedsM)   d.bedrooms  = parseInt(bedsM[1]);
  if (bathsM)  d.bathrooms = parseInt(bathsM[1]);
  if (areaM)   d.area      = parseInt(areaM[1]);
  if (priceM)  d.priceLow  = extractNumber(priceM[1]);
  var photoRe = /https?:\/\/cdn\.lecollectionist\.com\/[^\s"'<>]+\.(?:jpg|jpeg|png|webp)/gi;
  var photos = [], seen = {}, m;
  while ((m = photoRe.exec(html)) !== null) {
    if (!seen[m[0]]) { photos.push(m[0]); seen[m[0]] = true; }
  }
  d.photos = photos;
  d.amenityText = html;
  return d;
}

// ─── 3. Michael Zingraf ──────────────────────────────────────────────────────
function parseMichaelZingraf(html, url) {
  var d = {};
  d.title       = getMeta(html, 'og:title');
  d.description = getMeta(html, 'og:description');
  d.location    = matchLocation(url + ' ' + (d.title || ''));
  var bedsM  = html.match(/(\d+)\s*(?:bedroom|chambre)/i);
  var areaM  = html.match(/(\d+)\s*(?:sq\s*m|m[²2])/i);
  var priceM = html.match(/€\s*([\d\s,]+)\s*(?:per week|\/\s*week|la semaine)/i);
  if (bedsM)  d.bedrooms = parseInt(bedsM[1]);
  if (areaM)  d.area     = parseInt(areaM[1]);
  if (priceM) d.priceLow = extractNumber(priceM[1]);
  var photoRe = /https?:\/\/www\.michaelzingraf\.pro\/storage\/[^\s"'<>]+\.(?:jpg|jpeg|png|webp)/gi;
  var photos = [], seen = {}, m;
  while ((m = photoRe.exec(html)) !== null) {
    if (!seen[m[0]]) { photos.push(m[0]); seen[m[0]] = true; }
  }
  d.photos = photos;
  d.amenityText = html;
  return d;
}

// ─── 4. AMA Selections ──────────────────────────────────────────────────────
function parseAmaSelections(html, url) {
  var d = {};
  d.title       = getMeta(html, 'og:title');
  d.description = getMeta(html, 'og:description');
  d.location    = matchLocation(url + ' ' + (d.title || ''));
  var bedsM   = html.match(/(\d+)\s*(?:bedroom|chambre)/i);
  var bathsM  = html.match(/(\d+)\s*(?:bathroom|salle)/i);
  var guestsM = html.match(/(\d+)\s*(?:guests?|personnes?)/i);
  var areaM   = html.match(/(\d+)\s*m[²2]/i);
  var priceM  = html.match(/(?:from\s*)?€\s*([\d\s,]+)\s*\/\s*week/i);
  if (bedsM)   d.bedrooms  = parseInt(bedsM[1]);
  if (bathsM)  d.bathrooms = parseInt(bathsM[1]);
  if (guestsM) d.guests    = parseInt(guestsM[1]);
  if (areaM)   d.area      = parseInt(areaM[1]);
  if (priceM)  d.priceLow  = extractNumber(priceM[1]);
  var photoRe = /https?:\/\/ama-production[^\s"'<>]+\.(?:jpg|jpeg|png|webp)/gi;
  var photos = [], seen = {}, m;
  while ((m = photoRe.exec(html)) !== null) {
    if (!seen[m[0]]) { photos.push(m[0]); seen[m[0]] = true; }
  }
  d.photos = photos;
  d.amenityText = html;
  return d;
}

// ─── 5. Bo House ─────────────────────────────────────────────────────────────
function parseBoHouse(html, url) {
  var d = {};
  d.title       = getMeta(html, 'og:title');
  d.description = getMeta(html, 'og:description');
  d.location    = matchLocation(url + ' ' + (d.title || ''));
  var bedsM   = html.match(/(\d+)\s*(?:bedroom|chambre)/i);
  var guestsM = html.match(/(\d+)\s*(?:guests?|personnes?)/i);
  var areaM   = html.match(/(\d+)\s*m[²2]/i);
  var priceM  = html.match(/€\s*([\d\s,]+)\s*\/\s*(?:week|semaine)/i);
  if (bedsM)   d.bedrooms = parseInt(bedsM[1]);
  if (guestsM) d.guests   = parseInt(guestsM[1]);
  if (areaM)   d.area     = parseInt(areaM[1]);
  if (priceM)  d.priceLow = extractNumber(priceM[1]);
  d.photos = extractImages(html, 'https://bo-house.com');
  d.amenityText = html;
  return d;
}

// ─── 6. Résidences Immobilier ────────────────────────────────────────────────
function parseResidences(html, url) {
  var d = {};
  var h1 = html.match(/<h1[^>]*>([^<]+)<\/h1>/i);
  d.title       = getMeta(html, 'og:title') || (h1 ? decodeHtmlEntities(h1[1].trim()) : null);
  d.description = getMeta(html, 'og:description');

  var locM = url.match(/location-villa-([a-z-]+)-\d+\.html/i);
  if (locM) d.location = matchLocation(locM[1].replace(/-/g, ' ')) || matchLocation(url + ' ' + (d.title || ''));
  else      d.location = matchLocation(url + ' ' + (d.title || ''));

  var bedsM   = html.match(/(\d+)\s*chambre/i);
  var bathsM  = html.match(/(\d+)\s*salle/i);
  var guestsM = html.match(/(\d+)\s*personne/i);
  var areaM   = html.match(/([\d\s]+)\s*m[²2]/i);
  if (bedsM)   d.bedrooms  = parseInt(bedsM[1]);
  if (bathsM)  d.bathrooms = parseInt(bathsM[1]);
  if (guestsM) d.guests    = parseInt(guestsM[1]);
  if (areaM)   d.area      = parseInt(areaM[1].replace(/\s/g, ''));

  var priceM = html.match(/([\d][\d\s]*\d)\s*€\s*\/\s*semaine/i);
  if (priceM) d.priceLow = parseFloat(priceM[1].replace(/\s/g, ''));

  var photoRe = /https?:\/\/medias\.maisonsetappartements\.fr\/pict\/f1200x800\/[^\s"'<>]+\.(?:jpg|jpeg|png|webp)/gi;
  var photos = [], seen = {}, m;
  while ((m = photoRe.exec(html)) !== null) {
    if (!seen[m[0]]) { photos.push(m[0]); seen[m[0]] = true; }
  }
  d.photos = photos;
  d.amenityText = html;
  return d;
}

// ─── 7. Dôme Collection ─────────────────────────────────────────────────────
function parseDomeCollection(html, url) {
  var d = {};
  d.title       = getMeta(html, 'og:title') || getMeta(html, 'title');
  d.description = getMeta(html, 'og:description');
  d.location    = matchLocation(url + ' ' + (d.title || ''));

  var bedsM   = html.match(/(\d+)\s*chambre/i);
  var bathsM  = html.match(/(\d+)\s*[Ss]alle/i);
  var guestsM = html.match(/(\d+)\s*voyageur/i);
  var areaM   = html.match(/(\d+)\s*m[²2]/i);
  if (bedsM)   d.bedrooms  = parseInt(bedsM[1]);
  if (bathsM)  d.bathrooms = parseInt(bathsM[1]);
  if (guestsM) d.guests    = parseInt(guestsM[1]);
  if (areaM)   d.area      = parseInt(areaM[1]);

  var photoRe = /https?:\/\/dome-collection\.com\/wp-content\/uploads\/[^\s"'<>]+\.(?:jpg|jpeg|png|webp)/gi;
  var photos = [], seen = {}, m;
  while ((m = photoRe.exec(html)) !== null) {
    if (!seen[m[0]] && !/-(150|300)x/.test(m[0])) { photos.push(m[0]); seen[m[0]] = true; }
  }
  d.photos = photos;
  d.amenityText = html;
  return d;
}

// ─── 8. John Taylor ──────────────────────────────────────────────────────────
function parseJohnTaylor(html, url) {
  var d = {};
  d.title       = getMeta(html, 'og:title');
  d.description = getMeta(html, 'og:description');
  d.location    = matchLocation(url + ' ' + (d.title || ''));

  var bedsM    = html.match(/(\d+)\s*(?:bedroom|chambre)/i);
  var bathsM   = html.match(/(\d+)\s*(?:bathroom|salle de bain)/i);
  var areaM    = html.match(/(\d+)\s*m[²2]/i);
  var terraceM = html.match(/[Tt]errace[^:]*:\s*(\d+)\s*m[²2]/i)
              || html.match(/(\d+)\s*m[²2][^.]*terrasse/i);
  if (bedsM)    d.bedrooms  = parseInt(bedsM[1]);
  if (bathsM)   d.bathrooms = parseInt(bathsM[1]);
  if (areaM)    d.area      = parseInt(areaM[1]);
  if (terraceM) d.terrace   = parseInt(terraceM[1]);

  var priceMonthM = html.match(/([\d\s]+)\s*EUR\s*\/\s*Month/i);
  if (priceMonthM) d.priceLow = Math.round(parseFloat(priceMonthM[1].replace(/\s/g, '')) * 12 / 52);
  var priceWeekM = html.match(/([\d\s]+)\s*EUR\s*\/\s*[Ww]eek/i);
  if (priceWeekM) d.priceLow = parseFloat(priceWeekM[1].replace(/\s/g, ''));

  var photoRe = /https?:\/\/www\.john-taylor\.com\/rental-[^\s"'<>]+\.(?:jpg|jpeg|png|webp)/gi;
  var photos = [], seen = {}, m;
  while ((m = photoRe.exec(html)) !== null) {
    if (!seen[m[0]] && !/300x175/.test(m[0])) { photos.push(m[0]); seen[m[0]] = true; }
  }
  d.photos = photos;
  d.amenityText = html;
  return d;
}

// ─── 9. Generic (fallback) ───────────────────────────────────────────────────
function parseGeneric(html, url) {
  var d = {};
  d.title       = getMeta(html, 'og:title') || getMeta(html, 'title');
  d.description = getMeta(html, 'og:description') || getMeta(html, 'description');
  d.location    = matchLocation(url + ' ' + (d.title || ''));
  var jld = getJsonLd(html);
  if (jld) {
    d.description = d.description || jld.description;
    if (jld.numberOfRooms) d.bedrooms = parseInt(jld.numberOfRooms);
    if (jld.floorSize && jld.floorSize.value) d.area = parseInt(jld.floorSize.value);
    if (jld.offers && jld.offers.price) d.priceLow = parseFloat(jld.offers.price);
  }
  var bedsM   = html.match(/(\d+)\s*(?:bedroom|chambre)/i);
  var bathsM  = html.match(/(\d+)\s*(?:bathroom|salle de bain)/i);
  var guestsM = html.match(/(\d+)\s*(?:guests?|personnes?)/i);
  var areaM   = html.match(/(\d+)\s*m[²2]/i);
  var priceM  = html.match(/€\s*([\d\s,]+)\s*\/\s*(?:week|semaine)/i);
  if (bedsM)   d.bedrooms  = d.bedrooms  || parseInt(bedsM[1]);
  if (bathsM)  d.bathrooms = d.bathrooms || parseInt(bathsM[1]);
  if (guestsM) d.guests    = d.guests    || parseInt(guestsM[1]);
  if (areaM)   d.area      = d.area      || parseInt(areaM[1]);
  if (priceM)  d.priceLow  = d.priceLow  || extractNumber(priceM[1]);
  var baseUrl = url.match(/^(https?:\/\/[^\/]+)/);
  d.photos = extractImages(html, baseUrl ? baseUrl[1] : '');
  d.amenityText = html;
  return d;
}

// ─── Router ──────────────────────────────────────────────────────────────────
function detectAndParse(html, url) {
  if (url.indexOf('excellenceriviera.com') !== -1)     return parseExcellenceRiviera(html, url);
  if (url.indexOf('lecollectionist.com') !== -1)       return parseLecollectionist(html, url);
  if (url.indexOf('michaelzingraf') !== -1)            return parseMichaelZingraf(html, url);
  if (url.indexOf('amaselections.com') !== -1)         return parseAmaSelections(html, url);
  if (url.indexOf('bo-house.com') !== -1)              return parseBoHouse(html, url);
  if (url.indexOf('residences-immobilier.com') !== -1) return parseResidences(html, url);
  if (url.indexOf('dome-collection.com') !== -1)       return parseDomeCollection(html, url);
  if (url.indexOf('john-taylor.com') !== -1)           return parseJohnTaylor(html, url);
  return parseGeneric(html, url);
}

function uploadSourcePhotos(photos) {
  var uploaded = [];
  var limit = Math.min(photos.length, 25);
  for (var i = 0; i < limit; i++) {
    try {
      var cloudUrl = uploadToCloudinary(photos[i], null);
      uploaded.push({ url: cloudUrl });
      Utilities.sleep(500);
    } catch(e) { Logger.log('Photo upload error: ' + e); }
  }
  return uploaded;
}

// ═══════════════════════════════════════════════════════════════════════════
//  DUPLICATE DETECTION
// ═══════════════════════════════════════════════════════════════════════════

function normalizeTitle(str) {
  if (!str) return '';
  return str.toLowerCase()
    .replace(/villa|maison|domaine|château|chateau|propriété|propriete/gi, '')
    .replace(/[^a-z0-9\u00C0-\u024F\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function wordOverlap(a, b) {
  if (!a || !b) return 0;
  var wa = normalizeTitle(a).split(' ').filter(function(w) { return w.length >= 3; });
  var wb = normalizeTitle(b).split(' ').filter(function(w) { return w.length >= 3; });
  if (!wa.length || !wb.length) return 0;
  var matches = wa.filter(function(w) { return wb.indexOf(w) !== -1; }).length;
  return matches / Math.min(wa.length, wb.length);
}

function numClose(a, b, pct) {
  if (!a || !b) return false;
  return Math.abs(a - b) / Math.max(a, b) <= (pct / 100);
}

function checkDuplicates(parsed, existingRecords, skipId) {
  var warnings = [];
  existingRecords.forEach(function(r) {
    if (r.id === skipId) return;
    var f = r.fields || {};
    var score = 0;
    var reasons = [];

    var existingSource = f[FIELD_SOURCE] || '';
    if (existingSource && parsed.sourceUrl && existingSource === parsed.sourceUrl) {
      warnings.push('⚠️ EXACT SOURCE DUPLICATE: ' + r.id + ' (' + (f[FIELD_VILLA_NAME] || '') + ') — same Source URL');
      return;
    }

    var existingName  = f[FIELD_VILLA_NAME] || '';
    var existingTitle = f[TF_IDS[0].en] || '';
    var ovName  = wordOverlap(parsed.title, existingName);
    var ovTitle = wordOverlap(parsed.title, existingTitle);
    if (ovName >= 0.6)       { score += 3; reasons.push('name~' + Math.round(ovName * 100) + '%'); }
    else if (ovTitle >= 0.6) { score += 2; reasons.push('title~' + Math.round(ovTitle * 100) + '%'); }

    var existingLoc = f[FIELD_LOCATION];
    if (existingLoc && parsed.location) {
      var locName = typeof existingLoc === 'object' ? existingLoc.name : existingLoc;
      if (locName === parsed.location) { score += 2; reasons.push('location'); }
    }

    if (parsed.bedrooms  && f[FIELD_BEDROOMS]  && parsed.bedrooms  === f[FIELD_BEDROOMS])  { score += 2; reasons.push('beds='   + parsed.bedrooms); }
    if (parsed.bathrooms && f[FIELD_BATHROOMS] && parsed.bathrooms === f[FIELD_BATHROOMS]) { score += 1; reasons.push('baths='  + parsed.bathrooms); }
    if (parsed.guests    && f[FIELD_GUESTS]    && parsed.guests    === f[FIELD_GUESTS])    { score += 1; reasons.push('guests=' + parsed.guests); }
    if (numClose(parsed.area,      f[FIELD_AREA],       15)) { score += 1; reasons.push('area~'      + parsed.area      + 'm²'); }
    if (numClose(parsed.priceLow,  f[FIELD_PRICE_LOW],  25)) { score += 1; reasons.push('priceLow~€' + parsed.priceLow); }
    if (numClose(parsed.priceHigh, f[FIELD_PRICE_HIGH], 25)) { score += 1; reasons.push('priceHigh~€'+ parsed.priceHigh); }

    if (score >= 4) {
      warnings.push(
        '⚠️ Possible duplicate (' + score + ' pts): ' + r.id +
        ' (' + (f[FIELD_VILLA_NAME] || existingTitle || '?') + ')' +
        ' — ' + reasons.join(', ')
      );
    }
  });
  return warnings;
}

// ═══════════════════════════════════════════════════════════════════════════
//  FILL FROM SOURCE URL
// ═══════════════════════════════════════════════════════════════════════════

function fillFromSource(recordId, existingRecords) {
  var rec = fetchRecord(recordId);
  if (!rec || !rec.fields) return;
  var f = rec.fields;
  var sourceUrl = f[FIELD_SOURCE];
  if (!sourceUrl) return;

  Logger.log('fillFromSource: ' + sourceUrl);
  var html = fetchHtml(sourceUrl);
  if (!html) { Logger.log('Failed to fetch: ' + sourceUrl); return; }

  var d = detectAndParse(html, sourceUrl);
  d.sourceUrl = sourceUrl;
  Logger.log('Parsed: title=' + d.title + ' beds=' + d.bedrooms + ' photos=' + (d.photos ? d.photos.length : 0));

  var dupWarnings = existingRecords ? checkDuplicates(d, existingRecords, recordId) : [];
  if (dupWarnings.length) Logger.log('Duplicates: ' + dupWarnings.join(' | '));

  var patch = {};
  if (d.title       && !f[TF_IDS[0].en])    patch[TF_IDS[0].en]   = d.title;
  if (d.description && !f[TF_IDS[1].en])    patch[TF_IDS[1].en]   = d.description;
  if (d.location    && !f[FIELD_LOCATION])   patch[FIELD_LOCATION]  = d.location;
  if (d.bedrooms    && !f[FIELD_BEDROOMS])   patch[FIELD_BEDROOMS]  = d.bedrooms;
  if (d.bathrooms   && !f[FIELD_BATHROOMS])  patch[FIELD_BATHROOMS] = d.bathrooms;
  if (d.guests      && !f[FIELD_GUESTS])     patch[FIELD_GUESTS]    = d.guests;
  if (d.area        && !f[FIELD_AREA])       patch[FIELD_AREA]      = d.area;
  if (d.priceLow    && !f[FIELD_PRICE_LOW])  patch[FIELD_PRICE_LOW] = d.priceLow;
  if (d.priceHigh   && !f[FIELD_PRICE_HIGH]) patch[FIELD_PRICE_HIGH]= d.priceHigh;

  if (d.amenityText) {
    var amenities = mapAmenities(d.amenityText);
    if (amenities.equipements.length && !f[FIELD_EQUIPEMENTS]) patch[FIELD_EQUIPEMENTS] = amenities.equipements;
    if (amenities.building.length    && !f[FIELD_BUILDING])    patch[FIELD_BUILDING]    = amenities.building;
    if (amenities.security.length    && !f[FIELD_SECURITY])    patch[FIELD_SECURITY]    = amenities.security;
    if (amenities.sport.length       && !f[FIELD_SPORT])       patch[FIELD_SPORT]       = amenities.sport;
    if (amenities.exterior.length    && !f[FIELD_EXTERIOR])    patch[FIELD_EXTERIOR]    = amenities.exterior;
  }

  if (dupWarnings.length) {
    var existingNotes = f[FIELD_NOTES] || '';
    if (existingNotes.indexOf('Possible duplicate') === -1 && existingNotes.indexOf('EXACT SOURCE DUPLICATE') === -1) {
      patch[FIELD_NOTES] = existingNotes + '\n\n' + dupWarnings.join('\n');
    }
  }

  if (Object.keys(patch).length) { patchRecord(recordId, patch); Logger.log('Patched ' + Object.keys(patch).length + ' fields'); }

  if (d.photos && d.photos.length && (!f[FIELD_GALLERY_SRC] || !f[FIELD_GALLERY_SRC].length)) {
    Logger.log('Uploading ' + Math.min(d.photos.length, 25) + ' photos...');
    var uploaded = uploadSourcePhotos(d.photos);
    if (uploaded.length) { patchRecord(recordId, { [FIELD_GALLERY_SRC]: uploaded }); Logger.log('Gallery: ' + uploaded.length + ' photos uploaded'); }
  }

  Logger.log('✅ fillFromSource done: ' + (d.title || recordId));
}

function processSourceUrls() {
  var dupFields = [
    FIELD_SOURCE, FIELD_VILLA_NAME, TF_IDS[0].en,
    FIELD_LOCATION, FIELD_BEDROOMS, FIELD_BATHROOMS,
    FIELD_GUESTS, FIELD_AREA, FIELD_PRICE_LOW, FIELD_PRICE_HIGH
  ];
  var allRecords = fetchAllRecords(dupFields);
  var pending = allRecords.filter(function(r) {
    return r.fields && r.fields[FIELD_SOURCE] && !r.fields[TF_IDS[0].en] && !r.fields[FIELD_VILLA_NAME];
  });
  Logger.log('processSourceUrls: ' + pending.length + ' pending');
  if (!pending.length) return;
  fillFromSource(pending[0].id, allRecords);
}

// ─── Triggers ────────────────────────────────────────────────────────────────

function resetAllTriggers() {
  ScriptApp.getProjectTriggers().forEach(function(t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('processCheckboxPDF').timeBased().everyMinutes(1).create();
  ScriptApp.newTrigger('translateAll').timeBased().everyMinutes(15).create();
  ScriptApp.newTrigger('processNewImages').timeBased().everyMinutes(15).create();
  ScriptApp.newTrigger('cleanupStuckLocks').timeBased().everyHours(1).create();
  ScriptApp.newTrigger('processSourceUrls').timeBased().everyMinutes(5).create();
  Logger.log('Done: 5 triggers');
  ScriptApp.getProjectTriggers().forEach(function(t) { Logger.log('  → ' + t.getHandlerFunction()); });
}

// ─── Tests ───────────────────────────────────────────────────────────────────

function testRun() {
  runForRecord('recVoMtiJuVp7Zm4g');
}

function testFillFromSource() {
  fillFromSource('recVoMtiJuVp7Zm4g', null);
}
