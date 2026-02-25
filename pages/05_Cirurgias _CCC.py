import streamlit as st
import pdfplumber
import re
import io
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ─── Autenticação ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔐 Por favor autentique-se na página principal.")
    st.stop()

# ─── Constantes de parsing ────────────────────────────────────────────────────
PROC_MIN_X = 290
PROC_MAX_X = 480
DOC_MAX_X  = 290


# ─── Funções de parsing PDF ───────────────────────────────────────────────────

def cluster_rows(words, gap=6):
    if not words:
        return []
    sw = sorted(words, key=lambda w: w['top'])
    clusters = [[sw[0]]]
    for w in sw[1:]:
        if w['top'] - clusters[-1][-1]['top'] <= gap:
            clusters[-1].append(w)
        else:
            clusters.append([w])
    return [(int(c[0]['top']), c) for c in clusters]


def left_text(ws):
    return " ".join(
        w['text'] for w in sorted(ws, key=lambda x: x['x0'])
        if w['x0'] < DOC_MAX_X
    )


def proc_text(ws):
    return " ".join(
        w['text'] for w in sorted(ws, key=lambda x: x['x0'])
        if PROC_MIN_X <= w['x0'] < PROC_MAX_X
    )


def min_left_x(ws):
    lws = [w for w in ws if w['x0'] < DOC_MAX_X]
    return min(w['x0'] for w in lws) if lws else 0


def parse_cirurgias_pdf(pdf_bytes):
    records = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[1:]:
            words = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)
            row_clusters = cluster_rows(words, gap=6)

            date_re = re.compile(r'^\d{4}-\d{2}-\d{2}')
            gr_re   = re.compile(r'Gr\.\s*de\s*urg', re.I)
            resp_re = re.compile(r'Responsável:', re.I)

            row_data = [
                (top, left_text(ws), proc_text(ws), ws)
                for top, ws in row_clusters
            ]

            rec_starts = [
                i for i, (top, l, p, ws) in enumerate(row_data)
                if date_re.match(l) and re.search(r'CCC', l, re.I)
            ]

            for idx, start in enumerate(rec_starts):
                end = rec_starts[idx + 1] if idx + 1 < len(rec_starts) else len(row_data)
                block = row_data[start:end]

                _, first_left, first_proc, _ = block[0]

                dm = re.match(r'(\d{4}-\d{2}-\d{2})', first_left)
                date_raw = dm.group(1) if dm else ""
                pts = date_raw.split('-')
                date_fmt = f"{pts[2]}-{pts[1]}-{pts[0]}" if len(pts) == 3 else date_raw

                pm = re.search(r'CCC\s*/\s*(\d+)', first_left)
                proc_num = pm.group(1) if pm else ""

                nm = re.search(r'CCC\s*/\s*\d+\s*-\s*(.+)', first_left)
                name_acc = [nm.group(1).strip()] if nm else []

                urgency = ""
                proc_lines = [first_proc] if first_proc.strip() else []
                in_resp = False

                for top_row, left, right, row_ws in block[1:]:
                    if gr_re.search(left):
                        ug = re.search(r'urgência\s*:\s*(\w+)', left, re.I)
                        if ug:
                            urgency = ug.group(1)
                        in_resp = True
                        if right.strip():
                            proc_lines.append(right)
                        continue
                    if resp_re.search(left):
                        in_resp = True
                        if right.strip():
                            proc_lines.append(right)
                        continue
                    if in_resp:
                        mx = min_left_x(row_ws)
                        if mx > 145:
                            if right.strip():
                                proc_lines.append(right)
                            continue
                        else:
                            in_resp = False
                    if left.strip() and not re.search(r'\d{2}:\d{2}', left):
                        name_acc.append(left.strip())
                    if right.strip():
                        proc_lines.append(right)

                full_name = re.sub(r'\s+', ' ', " ".join(name_acc)).strip()

                proc_raw = " ".join(proc_lines)
                proc_raw = re.sub(r'\b\d+\b', '', proc_raw)
                proc_raw = re.sub(r'\s+', ' ', proc_raw).strip()

                proc_items = re.findall(
                    r'-([A-ZÁÉÍÓÚÀÃÕÂÊÔÇÜ][^-]+?)(?=\s*-[A-ZÁÉÍÓÚÀÃÕÂÊÔÇÜ]|$)',
                    proc_raw
                )
                procedures = []
                for p in proc_items:
                    p = re.sub(r'\s+', ' ', p).strip().strip(',').strip(' )')
                    if p and len(p) > 2 and not re.fullmatch(r'[\s/\(\)\.\)]+', p):
                        procedures.append(p)

                records.append({
                    "data":          date_fmt,
                    "processo":      proc_num,
                    "doente":        full_name,
                    "procedimentos": " | ".join(procedures),
                    "urgencia":      urgency,
                })

    return records


# ─── Funções Google Sheets ────────────────────────────────────────────────────

def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=scopes
    )
    return gspread.authorize(creds)


def append_to_sheets(records, sheet_url, pdf_name=""):
    """
    Abre a aba 'Cirurgias', encontra a primeira linha livre na coluna C
    e acrescenta os registos a partir daí sem apagar dados existentes.
    Se a aba não existir, cria-a com cabeçalhos.
    Se não houver linhas suficientes, expande a aba automaticamente.
    Devolve (primeira_linha_escrita, total_registos).
    """
    gc = get_gspread_client()
    sh = gc.open_by_url(sheet_url)

    # Obter ou criar aba Cirurgias
    try:
        ws = sh.worksheet("Cirurgias")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title="Cirurgias", rows=2000, cols=20)
        # Aba nova: escrever cabeçalhos na linha 1 a partir de C
        ws.update(
            range_name="C1:H1",
            values=[["Data", "Nº Processo", "Doente", "Procedimentos", "Urgência", "Origem"]]
        )
        ws.format("C1:H1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.122, "green": 0.220, "blue": 0.392},
        })

    # Primeira linha livre na coluna C
    col_c_values = ws.col_values(3)       # valores actuais da coluna C
    first_free_row = len(col_c_values) + 1

    # Construir linhas: colunas C a H (dados + nome do PDF de origem)
    rows_to_write = [
        [rec["data"], rec["processo"], rec["doente"], rec["procedimentos"], rec["urgencia"], pdf_name]
        for rec in records
    ]

    last_row = first_free_row + len(rows_to_write) - 1

    # Se a aba não tiver linhas suficientes, expande-a
    if last_row > ws.row_count:
        rows_needed = last_row - ws.row_count + 1000  # margem extra de segurança
        ws.add_rows(rows_needed)

    ws.update(
        range_name=f"C{first_free_row}:H{last_row}",
        values=rows_to_write
    )

    return first_free_row, len(rows_to_write)


# ─── Interface ────────────────────────────────────────────────────────────────

st.title("📋 Extração de Cirurgias — GHRO4045R")
st.markdown(
    "Carregue o PDF de **Cirurgias por Interveniente**. "
    "Os dados são extraídos e escritos automaticamente na aba **Cirurgias** "
    "da planilha configurada, a partir da primeira linha livre na coluna **C**."
)

st.divider()

sheet_url = st.session_state.get("sheet_url", "").strip()

if not sheet_url:
    st.warning(
        "⚠️ Nenhuma planilha configurada. "
        "Cole o link na barra lateral (⚙️ Configuração) antes de carregar o PDF."
    )

uploaded_file = st.file_uploader(
    "📂 Selecionar PDF",
    type=["pdf"],
    help="Relatório exportado do sistema GHRO4045R"
)

if uploaded_file:
    pdf_bytes = uploaded_file.read()

    # ── Parsing + escrita automática ──────────────────────────────────────────
    with st.spinner("🔍 A processar PDF..."):
        try:
            records = parse_cirurgias_pdf(pdf_bytes)
        except Exception as e:
            st.error(f"Erro ao processar PDF: {e}")
            st.stop()

    if not records:
        st.error("Não foi possível extrair registos. Confirme que é um relatório GHRO4045R válido.")
        st.stop()

    # ── Pré-visualização ──────────────────────────────────────────────────────
    import pandas as pd
    df = pd.DataFrame(records)
    df.columns = ["Data", "Nº Processo", "Doente", "Procedimentos", "Urgência"]

    def highlight_urgente(row):
        return (
            ["background-color: #ffe0e0"] * len(row)
            if row["Urgência"] == "Urgente"
            else [""] * len(row)
        )

    st.dataframe(
        df.style.apply(highlight_urgente, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Procedimentos": st.column_config.TextColumn(width="large"),
            "Doente":        st.column_config.TextColumn(width="medium"),
        }
    )

    col1, col2, col3, col4 = st.columns(4)
    urgentes = sum(1 for r in records if r["urgencia"] == "Urgente")
    with col1:
        st.metric("Total Cirurgias", len(records))
    with col2:
        st.metric("Dias Operatórios", len({r["data"] for r in records}))
    with col3:
        st.metric("Urgentes", urgentes)
    with col4:
        st.metric("Programadas", len(records) - urgentes)

    st.divider()

    # ── Escrita automática na planilha ────────────────────────────────────────
    if not sheet_url:
        st.info("Configure o link da planilha na barra lateral para exportar os dados.")
    else:
        st.caption(f"🔗 Planilha: `{sheet_url}`")
        with st.spinner("📤 A escrever na planilha..."):
            try:
                first_row, n = append_to_sheets(records, sheet_url, pdf_name=uploaded_file.name)
                st.success(
                    f"✅ **{n} registos** escritos na aba **Cirurgias** "
                    f"a partir da linha **{first_row}** (coluna C)."
                )
                st.markdown(f"[🔗 Abrir Planilha]({sheet_url})")
                st.session_state["last_sheet_write"] = {
                    "url":  sheet_url,
                    "rows": n,
                    "time": datetime.now().strftime("%d-%m-%Y %H:%M"),
                    "file": uploaded_file.name,
                }
            except gspread.exceptions.SpreadsheetNotFound:
                st.error("❌ Planilha não encontrada. Verifique o URL na configuração.")
            except gspread.exceptions.APIError as e:
                st.error(f"❌ Erro de API Google: {e}")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {e}")
                st.exception(e)

    last = st.session_state.get("last_sheet_write")
    if last:
        st.caption(
            f"📝 Última exportação: **{last['rows']} registos** "
            f"de `{last['file']}` → {last['time']}"
        )

else:
    st.info("👆 Carregue um ficheiro PDF para começar.")
