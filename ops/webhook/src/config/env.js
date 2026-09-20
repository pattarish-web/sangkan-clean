import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

/** Load ops/webhook/.env into process.env when keys are not already set. */
function loadDotEnv() {
  const candidates = [
    path.join(path.dirname(fileURLToPath(import.meta.url)), "../../.env"),
    path.join(path.dirname(fileURLToPath(import.meta.url)), "../../../../.env"),
    path.join(process.cwd(), ".env"),
  ];
  for (const file of candidates) {
    if (!existsSync(file)) continue;
    const text = readFileSync(file, "utf8");
    for (const raw of text.split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith("#")) continue;
      const eq = line.indexOf("=");
      if (eq <= 0) continue;
      const key = line.slice(0, eq).trim();
      let val = line.slice(eq + 1).trim();
      if (
        (val.startsWith('"') && val.endsWith('"')) ||
        (val.startsWith("'") && val.endsWith("'"))
      ) {
        val = val.slice(1, -1);
      }
      if (process.env[key] === undefined) process.env[key] = val;
    }
  }
}

loadDotEnv();

function required(name, fallback = "") {
  const v = process.env[name] ?? fallback;
  return v;
}

export function getConfig() {
  const ownerRaw = required("LINE_OWNER_USER_ID");
  return {
    port: Number(required("PORT", "3000")),
    line: {
      channelSecret: required("LINE_CHANNEL_SECRET"),
      channelAccessToken: required("LINE_CHANNEL_ACCESS_TOKEN"),
      ownerUserIds: ownerRaw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    },
    sheets: {
      spreadsheetId: required("GOOGLE_SHEETS_ID"),
      serviceAccountJson: required("GOOGLE_SERVICE_ACCOUNT_JSON"),
    },
    liff: {
      bookingId: required("LIFF_BOOKING_ID"),
      checkinId: required("LIFF_CHECKIN_ID"),
      powId: required("LIFF_POW_ID"),
    },
    gpsRadiusM: Number(required("GPS_RADIUS_M", "200")),
    affiliatePct: Number(required("AFFILIATE_PCT", "10")),
    /** Phase 1 Early Bird + Affiliate earning window (credits never expire). */
    promoPhase: Number(required("PROMO_PHASE", "1")),
    /** Inclusive Bangkok date YYYY-MM-DD; blank = open-ended */
    promoEndDate: required("PROMO_END_DATE", "2026-12-31"),
    publicBaseUrl: required("PUBLIC_BASE_URL", "http://localhost:3000").replace(
      /\/$/,
      ""
    ),
    richMenuIds: {
      customer: required("RICH_MENU_ID_CUSTOMER", ""),
      staff: required("RICH_MENU_ID_STAFF", ""),
      admin: required("RICH_MENU_ID_ADMIN", ""),
    },
    staffJoinCode: required("STAFF_JOIN_CODE", "sangkan-staff"),
    bankTransferInfo: required(
      "BANK_TRANSFER_INFO",
      "โอน PromptPay / บัญชีบริษัท ตามที่แอดมินแจ้งในแชท"
    ),
    /**
     * Root Drive folder for PoW photos.
     * Layout: root / YYYY-MM-DD / staffName / customerName / files
     * Prefer user OAuth (GOOGLE_DRIVE_REFRESH_TOKEN) for personal My Drive.
     * Service account works for Shared Drives only.
     */
    driveFolderId: required("GOOGLE_DRIVE_FOLDER_ID", ""),
    driveOAuth: {
      clientId: required("GOOGLE_DRIVE_CLIENT_ID", ""),
      clientSecret: required("GOOGLE_DRIVE_CLIENT_SECRET", ""),
      refreshToken: required("GOOGLE_DRIVE_REFRESH_TOKEN", ""),
    },
    leads: {
      staffToken: required("LEAD_STAFF_TOKEN", ""),
      allowedOrigins: required(
        "LEAD_ALLOWED_ORIGINS",
        "https://www.sangkanclean.com,https://sangkanclean.com"
      )
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      seedDemo: required("LEAD_SEED_DEMO", "") === "1",
      storeFile: required("LEAD_STORE_FILE", ""),
      publicApiUrl: required("LEAD_API_PUBLIC_URL", ""),
    },
    serveStaticRoot: required("SERVE_STATIC_ROOT", ""),
    trustProxy: required("TRUST_PROXY", "") === "1",
    googleAds: {
      developerToken: required("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
      clientId: required("GOOGLE_ADS_CLIENT_ID", ""),
      clientSecret: required("GOOGLE_ADS_CLIENT_SECRET", ""),
      refreshToken: required("GOOGLE_ADS_REFRESH_TOKEN", ""),
      customerId: required("GOOGLE_ADS_TARGET_CUSTOMER_ID", "6151208199"),
      loginCustomerId: required("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "7915729299"),
      apiVersion: required("GOOGLE_ADS_API_VERSION", "v19"),
    },
  };
}
