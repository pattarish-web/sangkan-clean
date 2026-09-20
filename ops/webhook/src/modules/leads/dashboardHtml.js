export function dashboardHtml() {
  return `<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>รายงานกิจกรรมรายวัน | Sangkan Clean</title>
  <meta name="robots" content="noindex, nofollow">
  <style>
    :root {
      --teal: #0d9488;
      --teal-dark: #0f766e;
      --ink: #0f172a;
      --muted: #64748b;
      --line: #e2e8f0;
      --bg: #f8fafc;
      --card: #fff;
      --good: #047857;
      --warn: #b45309;
      --bad: #b91c1c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Noto Sans Thai", "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      background: #fff;
      border-bottom: 1px solid var(--line);
      padding: 1rem 1.25rem;
      display: flex;
      flex-wrap: wrap;
      gap: .75rem 1.25rem;
      align-items: center;
      justify-content: space-between;
    }
    header h1 { font-size: 1.15rem; margin: 0; }
    header p { margin: .15rem 0 0; color: var(--muted); font-size: .9rem; }
    main { max-width: 1180px; margin: 0 auto; padding: 1.25rem; }
    .row { display: flex; flex-wrap: wrap; gap: .75rem; align-items: end; }
    label { font-size: .8rem; color: var(--muted); display: block; margin-bottom: .25rem; }
    input, select, button, textarea {
      font: inherit;
      padding: .55rem .7rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }
    button {
      background: var(--teal);
      color: #fff;
      border: 0;
      cursor: pointer;
      font-weight: 600;
    }
    button.secondary { background: #fff; color: var(--ink); border: 1px solid var(--line); }
    button:disabled { opacity: .5; cursor: default; }
    .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .75rem; margin: 1rem 0; }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 1rem;
    }
    .card strong { display: block; font-size: 1.45rem; margin-top: .2rem; }
    .muted { color: var(--muted); font-size: .85rem; }
    .bars { display: grid; gap: .45rem; }
    .bar { display: grid; grid-template-columns: 110px 1fr 40px; gap: .5rem; align-items: center; font-size: .85rem; }
    .bar i { display: block; height: 8px; background: var(--teal); border-radius: 99px; }
    table { width: 100%; border-collapse: collapse; font-size: .88rem; }
    th, td { text-align: left; padding: .65rem .5rem; border-bottom: 1px solid var(--line); vertical-align: top; }
    th { font-size: .75rem; color: var(--muted); font-weight: 600; }
    .status { display: inline-block; padding: .15rem .45rem; border-radius: 999px; font-size: .75rem; background: #e2e8f0; }
    .status.unverified { background: #ffedd5; color: #9a3412; }
    .status.new { background: #e0f2fe; }
    .status.contacted { background: #fef9c3; }
    .status.qualified, .status.quoted { background: #ccfbf1; }
    .status.won { background: #dcfce7; }
    .status.lost { background: #fee2e2; }
    .banner { padding: .85rem 1rem; border-radius: 10px; margin: 1rem 0; }
    .banner.error { background: #fef2f2; color: var(--bad); }
    .banner.ok { background: #ecfdf5; color: var(--good); }
    .banner.empty { background: #fff; border: 1px dashed var(--line); color: var(--muted); }
    .login { max-width: 420px; margin: 15vh auto; }
    .hidden { display: none; }
    .lead-name { font-weight: 600; }
    .tiny { font-size: .75rem; color: var(--muted); }
    @media (max-width: 720px) {
      table, thead, tbody, th, td, tr { display: block; }
      th { display: none; }
      td { border: 0; padding: .25rem 0; }
      tr { border: 1px solid var(--line); border-radius: 12px; padding: .8rem; margin-bottom: .75rem; background: #fff; }
    }
  </style>
</head>
<body>
  <div id="loginView" class="login card">
    <h1>รายงานกิจกรรมรายวัน</h1>
    <p class="muted">หน้านี้สำหรับฝ่ายขายเท่านั้น ใส่โทเคนพนักงานเพื่อดูลีด แหล่งโฆษณา และยอดปิดงาน</p>
    <form id="loginForm" style="display:grid;gap:.75rem;margin-top:1rem;">
      <div>
        <label for="token">โทเคนพนักงาน</label>
        <input id="token" name="token" type="password" required placeholder="LEAD_STAFF_TOKEN" autocomplete="current-password">
      </div>
      <button type="submit">เข้าสู่ระบบ</button>
      <p id="loginError" class="banner error hidden"></p>
      <p class="tiny">ค่าเริ่มต้นตอนพัฒนาท้องถิ่น: <code>sangkan-dev</code></p>
    </form>
  </div>

  <div id="appView" class="hidden">
    <header>
      <div>
        <h1>รายงานกิจกรรมรายวัน — Sangkan Clean</h1>
        <p>ยอดโฆษณาหลัก: โทรที่ยืนยัน · LINE ที่ยืนยัน · ฟอร์ม — คลิกดิบรอยืนยันก่อนส่ง Ads</p>
      </div>
      <div class="row">
        <a class="muted" href="/">เปิดเว็บไซต์</a>
        <button class="secondary" id="logoutBtn" type="button">ออกจากระบบ</button>
      </div>
    </header>
    <main>
      <div class="row">
        <div>
          <label for="date">วันที่ (เวลาไทย)</label>
          <input id="date" type="date">
        </div>
        <button type="button" id="reloadBtn">รีเฟรช</button>
        <button type="button" id="adsUploadBtn">ส่งคิวเข้า Google Ads</button>
        <a id="csvLink" class="muted" href="#">ดาวน์โหลดไฟล์สำรอง</a>
      </div>
      <p id="adsQueue" class="muted" style="margin:.75rem 0 0"></p>
      <p id="errorBox" class="banner error hidden"></p>
      <section class="kpis" id="kpis"></section>
      <div style="display:grid;grid-template-columns:minmax(240px,1fr) 2fr;gap:1rem;" class="layout">
        <section class="card">
          <h2 style="margin:0 0 .75rem;font-size:1rem;">แยกตามช่องทาง</h2>
          <div id="channels" class="bars"></div>
        </section>
        <section class="card">
          <h2 style="margin:0 0 .75rem;font-size:1rem;">สถานะขาย</h2>
          <div id="pipeline" class="kpis" style="margin:0"></div>
        </section>
      </div>
      <section style="margin-top:1rem;">
        <h2 style="font-size:1rem;">ลีดของวัน</h2>
        <div id="emptyBox" class="banner empty hidden">ยังไม่มีลีดในวันนี้ ลองเปลี่ยนวันที่ หรือส่งแบบฟอร์มขอใบเสนอราคาจากหน้าแรก</div>
        <div id="tableWrap" class="card" style="padding:0;overflow:auto;"></div>
      </section>
    </main>
  </div>
<script>
const STATUS_LABEL = {
  unverified: "คลิก—รอตรวจสอบ",
  new: "ลีดใหม่",
  contacted: "ติดต่อแล้ว",
  qualified: "ผ่านเกณฑ์",
  quoted: "ส่งราคา",
  won: "ปิดงาน",
  lost: "ไม่ปิด",
};
const CHANNEL_LABEL = {
  google_ads: "Google Ads",
  facebook: "Facebook",
  line: "LINE",
  organic: "Organic",
  referral: "Referral",
  direct: "Direct",
  tiktok: "TikTok",
};
const TOKEN_KEY = "sc_lead_staff_token";
const ERROR_LABEL = {
  confirm_name_required: "กรอกชื่อลูกค้าจากสายโทรหรือแชต LINE ก่อนยืนยัน",
  confirm_phone_required: "กรอกเบอร์ลูกค้าก่อนยืนยัน จึงจะส่ง Google Ads",
  phone_invalid: "เบอร์โทรไม่ถูกต้อง",
  won_requires_value: "ปิดงานต้องใส่มูลค่ามากกว่า 0",
  unauthorized: "ไม่มีสิทธิ์",
};
const loginView = document.getElementById("loginView");
const appView = document.getElementById("appView");
const dateEl = document.getElementById("date");
const errorBox = document.getElementById("errorBox");
const emptyBox = document.getElementById("emptyBox");

function todayBkk() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Bangkok" }).format(new Date());
}
function token() { return sessionStorage.getItem(TOKEN_KEY) || ""; }
function showError(msg, ok) {
  errorBox.textContent = msg || "";
  errorBox.classList.toggle("hidden", !msg);
  errorBox.classList.toggle("error", !ok);
  errorBox.classList.toggle("ok", Boolean(ok));
}
async function api(path, opts) {
  const headers = Object.assign({ Accept: "application/json" }, (opts && opts.headers) || {});
  headers.Authorization = "Bearer " + token();
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  if (res.status === 401) throw new Error("unauthorized");
  const type = res.headers.get("content-type") || "";
  const body = type.includes("json") ? await res.json() : await res.text();
  if (!res.ok) throw new Error((body && body.error) || ("http_" + res.status));
  return body;
}
function baht(n) {
  return Number(n || 0).toLocaleString("th-TH", { style: "currency", currency: "THB", maximumFractionDigits: 0 });
}
function showApp() {
  loginView.classList.add("hidden");
  appView.classList.remove("hidden");
  if (!dateEl.value) dateEl.value = todayBkk();
  document.getElementById("csvLink").removeAttribute("href");
  load();
}
async function load() {
  showError("");
  try {
    const date = dateEl.value;
    const [sumRes, listRes] = await Promise.all([
      api("/api/leads/summary?date=" + encodeURIComponent(date)),
      api("/api/leads?date=" + encodeURIComponent(date)),
    ]);
    renderSummary(sumRes.summary);
    renderTable(listRes.leads || []);
  } catch (err) {
    if (String(err.message) === "unauthorized") {
      sessionStorage.removeItem(TOKEN_KEY);
      location.reload();
      return;
    }
    showError("โหลดข้อมูลไม่สำเร็จ: " + err.message);
  }
}
function renderSummary(s) {
  const kpis = [
    ["กิจกรรมทั้งหมด", s.total],
    ["คลิกโทร", (s.byContactMethod && s.byContactMethod.phone) || 0],
    ["คลิก LINE", (s.byContactMethod && s.byContactMethod.line) || 0],
    ["แบบฟอร์ม", (s.byContactMethod && s.byContactMethod.form) || 0],
    ["รอตรวจสอบ", s.byStatus.unverified || 0],
    ["ลีดคุณภาพ", s.qualified],
    ["ปิดงาน", s.byStatus.won || 0],
    ["รายได้ที่ปิด", baht(s.revenue_thb)],
  ];
  document.getElementById("kpis").innerHTML = kpis.map(([k,v]) =>
    '<div class="card"><span class="muted">'+k+'</span><strong>'+v+'</strong></div>'
  ).join("");
  const ch = s.byChannel || {};
  const max = Math.max(1, ...Object.values(ch));
  const keys = Object.keys(ch);
  document.getElementById("channels").innerHTML = keys.length
    ? keys.map((k) => {
        const w = Math.round((ch[k] / max) * 100);
        return '<div class="bar"><span>'+(CHANNEL_LABEL[k]||k)+'</span><i style="width:'+w+'%"></i><span>'+ch[k]+'</span></div>';
      }).join("")
    : '<p class="muted">ยังไม่มีข้อมูลช่องทาง</p>';
  document.getElementById("pipeline").innerHTML = Object.keys(STATUS_LABEL).map((st) =>
    '<div class="card"><span class="muted">'+STATUS_LABEL[st]+'</span><strong>'+(s.byStatus[st]||0)+'</strong></div>'
  ).join("");
  const ads = s.adsUpload || {};
  document.getElementById("adsQueue").textContent =
    "คิว Google Ads (ทั้งหมด): รอส่ง " + (ads.pending || 0) +
    " · ส่งแล้ว " + (ads.uploaded || 0) +
    " · ล้มเหลว " + (ads.failed || 0) +
    " — กดยืนยันแล้วยิง API ทันที คิวนี้ใช้กดส่งซ้ำถ้าครั้งแรกไม่สำเร็จ";
}
function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function renderTable(leads) {
  emptyBox.classList.toggle("hidden", leads.length > 0);
  const wrap = document.getElementById("tableWrap");
  if (!leads.length) { wrap.innerHTML = ""; return; }
  wrap.innerHTML = '<table><thead><tr><th>ลูกค้า</th><th>บริการ</th><th>ต้นทาง</th><th>สถานะ</th><th>มูลค่า / Ads</th></tr></thead><tbody>' +
    leads.map((lead) => {
      const attr = lead.attribution || {};
      const methodLabel = lead.contact_method === "phone"
        ? "คลิกโทร"
        : lead.contact_method === "line"
          ? "คลิก LINE"
          : "แบบฟอร์ม";
      const created = lead.created_at
        ? new Date(lead.created_at).toLocaleString("th-TH", { timeZone: "Asia/Bangkok" })
        : "";
      const opts = Object.keys(STATUS_LABEL).map((st) =>
        '<option value="'+st+'"'+(lead.status===st?' selected':'')+'>'+STATUS_LABEL[st]+'</option>'
      ).join("");
      const isClick = lead.contact_method === "phone" || lead.contact_method === "line";
      const adsNote = lead.ads_contact_sent_at
        ? "ส่ง Google Ads แล้ว"
        : lead.ads_qualified_sent_at
          ? "ส่งลีดคุณภาพแล้ว"
          : (isClick && lead.status === "unverified" && attr.gclid)
            ? "รอยืนยันก่อนส่ง Ads"
            : (isClick && !attr.gclid)
              ? "ไม่มี GCLID — ไม่ส่ง Ads"
              : (attr.gclid ? "มี GCLID" : "ไม่มี GCLID");
      const saveLabel = isClick && lead.status === "unverified" ? "ยืนยัน" : "บันทึก";
      const hint = isClick && lead.status === "unverified"
        ? '<div class="tiny">เทียบเวลาในมือถือ/LINE แล้วกรอกชื่อ-เบอร์ เลือกสถานะอย่างน้อย “ติดต่อแล้ว” จึงจะส่ง Google Ads</div>'
        : "";
      return '<tr data-id="'+escapeHtml(lead.id)+'">'+
        '<td><span class="status '+escapeHtml(lead.status)+'">'+escapeHtml(methodLabel)+'</span>'+
          '<div class="tiny" style="margin:.3rem 0">'+escapeHtml(created)+' · '+escapeHtml(lead.id)+'</div>'+
          '<label class="tiny" for="name-'+escapeHtml(lead.id)+'">ชื่อลูกค้า</label>'+
          '<input id="name-'+escapeHtml(lead.id)+'" class="lead-name-input" name="lead_name" autocomplete="name" placeholder="ชื่อจากสายโทรหรือแชต LINE" value="'+escapeHtml(lead.name||"")+'">'+
          '<label class="tiny" for="phone-'+escapeHtml(lead.id)+'">เบอร์โทร</label>'+
          '<input id="phone-'+escapeHtml(lead.id)+'" class="lead-phone-input" name="lead_phone" autocomplete="tel" inputmode="tel" placeholder="0XXXXXXXXX" value="'+escapeHtml(lead.phone||"")+'" style="margin-top:.15rem">'+
          '<label class="tiny" for="area-'+escapeHtml(lead.id)+'">พื้นที่</label>'+
          '<input id="area-'+escapeHtml(lead.id)+'" class="lead-area-input" name="lead_area" placeholder="เช่น บางนา" value="'+escapeHtml(lead.area||"")+'" style="margin-top:.15rem">'+hint+'</td>'+
        '<td><input class="lead-service-input" value="'+escapeHtml(lead.service||"")+'"><div class="tiny">'+escapeHtml((lead.message||"").slice(0,80))+'</div></td>'+
        '<td><span class="status">'+escapeHtml(CHANNEL_LABEL[attr.channel]||attr.channel||"direct")+'</span>'+
          '<div class="tiny">'+(attr.gclid ? "GCLID "+escapeHtml(attr.gclid.slice(0,16))+"…" : "ไม่มี GCLID")+'</div>'+
          '<div class="tiny">'+escapeHtml(attr.utm_campaign||attr.keyword||attr.landing_page||"")+'</div></td>'+
        '<td><select class="st">'+opts+'</select><div class="tiny" style="margin-top:.35rem;"><input class="lost" placeholder="เหตุผลที่ไม่ปิด" value="'+escapeHtml(lead.lost_reason||"")+'"></div></td>'+
        '<td><input class="val" type="number" min="0" step="100" value="'+(lead.value_thb||"")+'" placeholder="บาท">'+
          '<div class="tiny" style="margin-top:.35rem;">'+escapeHtml(adsNote)+'</div>'+
          '<div style="margin-top:.4rem;"><button type="button" class="save">'+saveLabel+'</button></div></td>'+
      '</tr>';
    }).join("") + "</tbody></table>";
  wrap.querySelectorAll(".save").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const tr = btn.closest("tr");
      btn.disabled = true;
      try {
        const isConfirm = btn.textContent.trim() === "ยืนยัน";
        let status = tr.querySelector(".st").value;
        const name = tr.querySelector(".lead-name-input").value;
        const phone = tr.querySelector(".lead-phone-input").value;
        if (isConfirm && status === "unverified") {
          status = "contacted";
        }
        const value_thb = tr.querySelector(".val").value;
        const lost_reason = tr.querySelector(".lost").value;
        const service = tr.querySelector(".lead-service-input").value;
        const area = tr.querySelector(".lead-area-input").value;
        await api("/api/leads/" + encodeURIComponent(tr.dataset.id), {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status, value_thb, lost_reason, name, phone, service, area }),
        });
        await load();
      } catch (err) {
        showError("บันทึกไม่สำเร็จ: " + (ERROR_LABEL[err.message] || err.message));
        btn.disabled = false;
      }
    });
  });
}
document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const value = document.getElementById("token").value.trim();
  const box = document.getElementById("loginError");
  sessionStorage.setItem(TOKEN_KEY, value);
  try {
    await api("/api/leads/summary?date=" + encodeURIComponent(todayBkk()));
    box.classList.add("hidden");
    showApp();
  } catch (err) {
    sessionStorage.removeItem(TOKEN_KEY);
    box.textContent = "โทเคนไม่ถูกต้อง";
    box.classList.remove("hidden");
  }
});
document.getElementById("logoutBtn").addEventListener("click", () => {
  sessionStorage.removeItem(TOKEN_KEY);
  location.reload();
});
document.getElementById("reloadBtn").addEventListener("click", load);
document.getElementById("csvLink").addEventListener("click", async (e) => {
  e.preventDefault();
  try {
    const res = await fetch("/api/leads/ads-conversions.csv", {
      headers: { Authorization: "Bearer " + token(), Accept: "text/csv" },
    });
    if (res.status === 401) throw new Error("unauthorized");
    if (!res.ok) throw new Error("http_" + res.status);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sangkan-ads-conversions.csv";
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showError("ดาวน์โหลดไฟล์สำรองไม่สำเร็จ: " + (ERROR_LABEL[err.message] || err.message));
  }
});
document.getElementById("adsUploadBtn").addEventListener("click", async () => {
  const btn = document.getElementById("adsUploadBtn");
  btn.disabled = true;
  try {
    const res = await api("/api/leads/ads-conversions/upload", { method: "POST" });
    const upload = (res && res.ads_upload) || {};
    await load();
    if (upload.failed) {
      showError("ส่งคิว Ads ไม่ครบ: สำเร็จ " + (upload.uploaded || 0) + " ล้มเหลว " + upload.failed);
    } else if (upload.skipped) {
      const reason = upload.reason === "not_configured"
        ? "ยังไม่ได้ตั้งค่า Google Ads API บนเซิร์ฟเวอร์ — คิวถูกเก็บไว้"
        : "ไม่มีรายการรอส่ง";
      showError(reason, true);
    } else {
      showError("ส่งเข้า Google Ads แล้ว " + (upload.uploaded || 0) + " รายการ", true);
    }
  } catch (err) {
    showError("ส่งคิว Ads ไม่สำเร็จ: " + (ERROR_LABEL[err.message] || err.message));
  } finally {
    btn.disabled = false;
  }
});
dateEl.addEventListener("change", load);
if (token()) showApp();
</script>
</body>
</html>`;
}
