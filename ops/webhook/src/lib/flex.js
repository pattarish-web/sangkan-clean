import { PACKAGES } from "../config/packages.js";

const SITE = "https://www.sangkanclean.com";

export const SERVICE_URLS = {
  bigclean: `${SITE}/landing-bigcleaning.html`,
  maid: `${SITE}/landing-maid.html`,
  office: `${SITE}/landing-sangkan-office.html`,
};

/** First-touch chooser: Big Clean / แม่บ้านประจำ / Sangkan Office */
export function serviceChooserFlex() {
  return {
    type: "flex",
    altText: "เลือกบริการ Sangkan Clean",
    contents: {
      type: "bubble",
      size: "mega",
      body: {
        type: "box",
        layout: "vertical",
        spacing: "md",
        contents: [
          {
            type: "text",
            text: "Sangkan Clean",
            weight: "bold",
            size: "xl",
            color: "#0f172a",
          },
          {
            type: "text",
            text: "สนใจบริการแบบไหนครับ? เลือกด้านล่างได้เลย",
            size: "sm",
            color: "#64748b",
            wrap: true,
          },
          { type: "separator", margin: "md" },
          serviceRow(
            "Big Cleaning",
            "ทำความสะอาดใหญ่ บ้าน/คอนโด/ออฟฟิศ ครั้งคราว",
            "เลือก Big Clean",
            "action=choose_service&service=bigclean",
            "สนใจ Big Cleaning"
          ),
          serviceRow(
            "แม่บ้านประจำ",
            "แม่บ้านรายเดือน / จ้างประจำตามแพ็คเกจปกติ",
            "เลือกแม่บ้านประจำ",
            "action=choose_service&service=maid",
            "สนใจแม่บ้านประจำ"
          ),
          serviceRow(
            "Sangkan Office",
            "ออฟฟิศรายเดือนโซนอุดมสุข · แพ็คเกจ S/M/L + Early Bird",
            "เลือก Office",
            "action=choose_service&service=office",
            "สนใจ Sangkan Office"
          ),
        ],
      },
    },
  };
}

function serviceRow(title, desc, buttonLabel, data, displayText) {
  return {
    type: "box",
    layout: "vertical",
    margin: "lg",
    spacing: "sm",
    contents: [
      {
        type: "text",
        text: title,
        weight: "bold",
        size: "md",
        color: "#0d9488",
      },
      {
        type: "text",
        text: desc,
        size: "xs",
        color: "#64748b",
        wrap: true,
      },
      {
        type: "button",
        style: "primary",
        color: "#0d9488",
        height: "sm",
        margin: "sm",
        action: {
          type: "postback",
          label: buttonLabel,
          data,
          displayText,
        },
      },
    ],
  };
}

export function packagesFlex() {
  const bubbles = ["S", "M", "L"].map((id) => {
    const p = PACKAGES[id];
    const combo =
      id === "M"
        ? "รวม Mini Deep + โอโซน สิ้นเดือน (รอบพิเศษ)"
        : id === "L"
          ? "รวม Full Big Clean ทุก 2 เดือน (รอบพิเศษ)"
          : "ไม่มี Combo";
    return {
      type: "bubble",
      size: "kilo",
      body: {
        type: "box",
        layout: "vertical",
        contents: [
          {
            type: "text",
            text: id === "M" ? "แนะนำ" : p.id,
            weight: "bold",
            color: id === "M" ? "#0d9488" : "#64748b",
            size: "sm",
          },
          {
            type: "text",
            text: p.name,
            weight: "bold",
            size: "lg",
            margin: "md",
          },
          {
            type: "text",
            text: `฿${p.price.toLocaleString("th-TH")}/เดือน`,
            size: "xl",
            weight: "bold",
            margin: "md",
            color: "#0f172a",
          },
          {
            type: "text",
            text: `${p.visitsPerWeek} ครั้ง/สัปดาห์ (${p.routinePerMonth} รอบปกติ)`,
            size: "sm",
            color: "#64748b",
            margin: "md",
            wrap: true,
          },
          {
            type: "text",
            text: combo,
            size: "xs",
            color: "#64748b",
            margin: "sm",
            wrap: true,
          },
        ],
      },
      footer: {
        type: "box",
        layout: "vertical",
        contents: [
          {
            type: "button",
            style: id === "M" ? "primary" : "secondary",
            color: id === "M" ? "#0d9488" : undefined,
            action: {
              type: "postback",
              label: `เลือก ${p.id}`,
              data: `action=select_package&package=${p.id}`,
              displayText: `สนใจแพ็คเกจ ${p.name}`,
            },
          },
        ],
      },
    };
  });

  return {
    type: "flex",
    altText: "แพ็คเกจ Sangkan Office S / M / L",
    contents: { type: "carousel", contents: bubbles },
  };
}

export function thresholdFlex(stats) {
  const { counts, revenue, hireReady, lines } = stats;
  return {
    type: "flex",
    altText: "ยอดจอง / Threshold",
    contents: {
      type: "bubble",
      body: {
        type: "box",
        layout: "vertical",
        contents: [
          {
            type: "text",
            text: "ยอดจอง Early Bird",
            weight: "bold",
            size: "lg",
          },
          {
            type: "text",
            text: hireReady ? "ถึงเกณฑ์จ้างได้แล้ว" : "ยังไม่ถึงเกณฑ์จ้าง",
            color: hireReady ? "#0d9488" : "#f59e0b",
            size: "sm",
            margin: "md",
          },
          {
            type: "separator",
            margin: "lg",
          },
          {
            type: "box",
            layout: "vertical",
            margin: "lg",
            spacing: "sm",
            contents: [
              row("S Lite", `${counts.S} ราย`),
              row("M Growth", `${counts.M} ราย`),
              row("L Premium", `${counts.L} ราย`),
              row("รายได้จอง", `฿${revenue.toLocaleString("th-TH")}`),
            ],
          },
          {
            type: "text",
            text: lines.join(" · "),
            size: "xs",
            color: "#94a3b8",
            margin: "lg",
            wrap: true,
          },
        ],
      },
    },
  };
}

function row(label, value) {
  return {
    type: "box",
    layout: "horizontal",
    contents: [
      { type: "text", text: label, size: "sm", color: "#64748b", flex: 2 },
      {
        type: "text",
        text: value,
        size: "sm",
        weight: "bold",
        align: "end",
        flex: 2,
      },
    ],
  };
}

export function jobListFlex(title, jobs, customersById) {
  const items =
    jobs.length === 0
      ? [
          {
            type: "text",
            text: "ไม่มีงานในรายการ",
            size: "sm",
            color: "#94a3b8",
          },
        ]
      : jobs.slice(0, 10).map((j) => {
          const c = customersById[j.customer_id];
          const name = c?.company_name || j.customer_id;
          const flag =
            j.type === "combo_mini_deep"
              ? " [Mini Deep]"
              : j.type === "combo_full_big"
                ? " [Full Big]"
                : "";
          return {
            type: "box",
            layout: "vertical",
            margin: "md",
            contents: [
              {
                type: "text",
                text: `${j.time_slot || "—"} ${name}${flag}`,
                size: "sm",
                weight: "bold",
                wrap: true,
              },
              {
                type: "text",
                text: `สถานะ: ${j.status} · ${j.id}`,
                size: "xs",
                color: "#64748b",
              },
            ],
          };
        });

  return {
    type: "flex",
    altText: title,
    contents: {
      type: "bubble",
      body: {
        type: "box",
        layout: "vertical",
        contents: [
          { type: "text", text: title, weight: "bold", size: "lg" },
          ...items,
        ],
      },
    },
  };
}

export function billFlex({
  paymentId,
  companyName,
  typeLabel,
  packageId,
  amount,
  creditApplied,
  depositApplied,
  payable,
  bankInfo,
}) {
  const rows = [
    row("บริษัท", companyName || "—"),
    row("ประเภท", typeLabel),
  ];
  if (packageId) rows.push(row("แพ็คเกจ", packageId));
  rows.push(row("ยอดเต็ม", `฿${Number(amount).toLocaleString("th-TH")}`));
  if (depositApplied > 0) {
    rows.push(row("หักมัดจำ", `-฿${Number(depositApplied).toLocaleString("th-TH")}`));
  }
  if (creditApplied > 0) {
    rows.push(row("หักเครดิต", `-฿${Number(creditApplied).toLocaleString("th-TH")}`));
  }
  rows.push(row("ยอดโอน", `฿${Number(payable).toLocaleString("th-TH")}`));

  return {
    type: "flex",
    altText: `บิล ${paymentId} ยอดโอน ฿${payable}`,
    contents: {
      type: "bubble",
      body: {
        type: "box",
        layout: "vertical",
        contents: [
          {
            type: "text",
            text: "ใบแจ้งยอดชำระ",
            weight: "bold",
            size: "lg",
          },
          {
            type: "text",
            text: paymentId,
            size: "xs",
            color: "#94a3b8",
            margin: "sm",
          },
          { type: "separator", margin: "lg" },
          {
            type: "box",
            layout: "vertical",
            margin: "lg",
            spacing: "sm",
            contents: rows,
          },
          {
            type: "text",
            text: bankInfo || "โอนตามที่แอดมินแจ้ง",
            size: "xs",
            color: "#64748b",
            margin: "lg",
            wrap: true,
          },
        ],
      },
      footer: {
        type: "box",
        layout: "vertical",
        contents: [
          {
            type: "text",
            text:
              Number(payable) > 0
                ? "โอนแล้วส่งรูปสลิปในแชทนี้"
                : "ยอด 0 — รอแอดมินยืนยันปิดบิล",
            size: "sm",
            align: "center",
            color: "#0d9488",
            wrap: true,
          },
        ],
      },
    },
  };
}

export function pendingPaymentAdminFlex({
  paymentId,
  companyName,
  payable,
  typeLabel,
  note,
}) {
  return {
    type: "flex",
    altText: `รอตรวจสลิป ${paymentId}`,
    contents: {
      type: "bubble",
      body: {
        type: "box",
        layout: "vertical",
        contents: [
          {
            type: "text",
            text: "รอตรวจชำระ",
            weight: "bold",
            size: "lg",
          },
          {
            type: "text",
            text: `${companyName}\n${typeLabel} · ฿${Number(payable).toLocaleString("th-TH")}\n${paymentId}`,
            size: "sm",
            color: "#64748b",
            margin: "md",
            wrap: true,
          },
          ...(note
            ? [
                {
                  type: "text",
                  text: note,
                  size: "xs",
                  color: "#94a3b8",
                  margin: "sm",
                  wrap: true,
                },
              ]
            : []),
        ],
      },
      footer: {
        type: "box",
        layout: "vertical",
        spacing: "sm",
        contents: [
          {
            type: "button",
            style: "primary",
            color: "#0d9488",
            action: {
              type: "postback",
              label: "ยืนยันชำระ",
              data: `action=billing_confirm&payment_id=${paymentId}`,
              displayText: `ยืนยัน ${paymentId}`,
            },
          },
          {
            type: "button",
            style: "secondary",
            action: {
              type: "postback",
              label: "ปฏิเสธ",
              data: `action=billing_reject&payment_id=${paymentId}`,
              displayText: `ปฏิเสธ ${paymentId}`,
            },
          },
        ],
      },
    },
  };
}
