import streamlit as st
import pandas as pd
import time
from cleaner import clean_dataframe, load_file, to_csv_bytes, generate_pandas_script
from ai_insights import get_ai_insights

st.set_page_config(
    page_title="DataHealer AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #00d4ff;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 1rem;
        color: #94a3b8;
        margin-top: -12px;
        margin-bottom: 28px;
    }
    .metric-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 12px;
    }
    .insight-card {
        background: #0f172a;
        border-left: 3px solid #00d4ff;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        color: #e2e8f0;
        font-size: 0.93rem;
    }
    .action-card {
        background: #0a1628;
        border-left: 3px solid #f59e0b;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        color: #e2e8f0;
        font-size: 0.93rem;
    }
    .risk-card {
        background: #0f172a;
        border-left: 3px solid #ef4444;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        color: #e2e8f0;
        font-size: 0.93rem;
    }
    .score-ring {
        font-size: 3rem;
        font-weight: 900;
        color: #00d4ff;
    }
    div[data-testid="stDownloadButton"] > button {
        background-color: #0ea5e9;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        width: 100%;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #0284c7;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="main-title">🩺 DataHealer AI</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sub-title">Drop any dirty CSV or Excel file. '
            'Get a production-ready cleaned dataset, Python script, and AI-powered business insights — instantly.</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Built with Python · Pandas · Pydantic · Gemini API")


def render_upload_zone():
    st.markdown("### 📂 Upload Your Dataset")
    uploaded = st.file_uploader(
        "Drag and drop or browse a file",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )
    return uploaded


def render_metrics(report):
    st.markdown("### 📊 Cleaning Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Rows (Clean)", f"{report.total_rows:,}")
    c2.metric("🔧 Nulls Fixed", f"{report.null_cells_fixed:,}")
    c3.metric("🗑️ Duplicates Removed", f"{report.duplicate_rows_removed:,}")
    c4.metric("📅 Date Columns Fixed", len(report.date_columns_fixed))


def render_ai_panel(insights: dict):
    st.markdown("### 🤖 AI Insights Panel")
    score = insights.get("quality_score", 0)
    snapshot = insights.get("data_snapshot", "")

    col_score, col_snap = st.columns([1, 3])
    with col_score:
        color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
        st.markdown(
            f'<div style="text-align:center; padding: 20px;">'
            f'<div style="font-size:3rem; font-weight:900; color:{color};">{score}</div>'
            f'<div style="color:#94a3b8; font-size:0.85rem;">Data Quality Score</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_snap:
        st.info(snapshot)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**💡 Top Insights**")
        for item in insights.get("top_insights", []):
            st.markdown(f'<div class="insight-card">📌 {item}</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown("**⚡ Executive Action Brief**")
        for item in insights.get("action_brief", []):
            st.markdown(f'<div class="action-card">▶ {item}</div>', unsafe_allow_html=True)

    flags = insights.get("risk_flags", [])
    if flags and flags[0].lower() not in ("none", "none detected"):
        st.markdown("**🚨 Risk Flags**")
        for flag in flags:
            st.markdown(f'<div class="risk-card">⚠️ {flag}</div>', unsafe_allow_html=True)


def render_downloads(cleaned_df, report, original_df):
    st.markdown("### 📥 Download Your Results")
    c1, c2 = st.columns(2)

    with c1:
        csv_bytes = to_csv_bytes(cleaned_df)
        st.download_button(
            label="⬇️ Download Cleaned CSV",
            data=csv_bytes,
            file_name="datahealer_cleaned.csv",
            mime="text/csv",
        )

    with c2:
        script = generate_pandas_script(
            cleaned_df,
            report.date_columns_fixed,
            report.type_issues_fixed,
        )
        st.download_button(
            label="⬇️ Download Python Script",
            data=script.encode("utf-8"),
            file_name="datahealer_pipeline.py",
            mime="text/x-python",
        )


def render_preview(original_df, cleaned_df):
    st.markdown("### 🔍 Data Preview")
    tab1, tab2 = st.tabs(["✅ Cleaned Dataset", "⚠️ Original (Raw)"])
    with tab1:
        st.dataframe(cleaned_df.head(50), use_container_width=True)
    with tab2:
        st.dataframe(original_df.head(50), use_container_width=True)


def main():
    render_header()
    st.divider()

    uploaded = render_upload_zone()

    if uploaded is not None:
        try:
            with st.spinner("Reading your file..."):
                original_df = load_file(uploaded)

            st.success(f"Loaded **{len(original_df):,} rows × {len(original_df.columns)} columns**")

            with st.spinner("Cleaning data with Python + Pydantic validation..."):
                time.sleep(0.6)
                cleaned_df, report = clean_dataframe(original_df.copy())

            render_metrics(report)
            st.divider()

            with st.spinner("Analyzing with Gemini AI..."):
                sample_rows = cleaned_df.head(5).to_dict(orient="records")
                insights = get_ai_insights(
                    list(cleaned_df.columns),
                    sample_rows,
                    report.summary,
                )

            render_ai_panel(insights)
            st.divider()

            render_downloads(cleaned_df, report, original_df)
            st.divider()

            render_preview(original_df, cleaned_df)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.caption("Make sure your file is a valid CSV or Excel file with headers in the first row.")

    else:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color: #475569;">
            <div style="font-size: 3rem;">📁</div>
            <div style="font-size: 1.1rem; margin-top: 10px;">
                Upload a CSV or Excel file to get started
            </div>
            <div style="font-size: 0.85rem; margin-top: 8px; color: #64748b;">
                Supports broken dates · duplicate rows · mixed types · missing values
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
