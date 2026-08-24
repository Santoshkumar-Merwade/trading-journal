import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
from PIL import Image

# ==================== CONFIGURATION & SETUP ==================== #

EXCEL_FILE = "swing_trading_journal.xlsx"
CHARTS_DIR = "trade_charts"

# Ensure image storage directory exists
os.makedirs(CHARTS_DIR, exist_ok=True)

COLUMNS = [
    "Trade Number", "Date of Entry", "Date of Exit", "Holding Days",
    "Total Capital", "Capital Deployed", "Scrip Name", "Position Type",
    "Position Size/Quantity", "Entry Price", "Exit Price", "Stop Loss Level",
    "Trail SL Level", "Risk-Reward Ratio", "Trade Duration", "Trading Strategy Used",
    "Reason for Entering", "Technical Setup", "Fundamental Factors", "Market Conditions",
    "Stop Loss Adjustment", "Take Profit Adjustment", "Partial Exit",
    "How Did You Feel", "Stick to Plan", "Emotional Triggers", "Decision-Making Notes",
    "Profit or Loss", "Trade Outcome", "Reason for Success/Failure", "Key Takeaways", 
    "Improvement Areas", "Chart Path"
]

st.set_page_config(page_title="Swing Trading Journal & Chart Viewer", page_icon="📈", layout="wide")

# ==================== DATA PERSISTENCE ==================== #

def init_excel():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_excel(EXCEL_FILE, index=False)

def load_data():
    init_excel()
    df = pd.read_excel(EXCEL_FILE)
    
    # Ensure missing columns (like Chart Path) are backfilled if reading an older spreadsheet
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
            
    if not df.empty:
        df['Date of Entry'] = pd.to_datetime(df['Date of Entry']).dt.date
        df['Date of Exit'] = pd.to_datetime(df['Date of Exit']).dt.date
    return df

def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)

def save_chart_image(uploaded_file, trade_num):
    """Saves the uploaded chart image file and returns the saved file path."""
    if uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"trade_{trade_num}{file_ext}"
        filepath = os.path.join(CHARTS_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath
    return ""

# ==================== METRICS CALCULATOR ==================== #

def calculate_metrics(df):
    if df.empty:
        return {
            "Total Trades": 0, "Win Rate (%)": "0%", "Net P&L": "0.00",
            "Avg Gain": "0.00", "Avg Loss": "0.00", "Avg R:R": "0.00",
            "Largest Win": "0.00", "Largest Loss": "0.00", "Max Drawdown": "0.00"
        }
    
    total_trades = len(df)
    wins = df[df['Profit or Loss'] > 0]
    losses = df[df['Profit or Loss'] < 0]
    
    win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
    avg_gain = wins['Profit or Loss'].mean() if not wins.empty else 0
    avg_loss = losses['Profit or Loss'].mean() if not losses.empty else 0
    net_pnl = df['Profit or Loss'].sum()
    largest_win = df['Profit or Loss'].max()
    largest_loss = df['Profit or Loss'].min()
    avg_rr = df['Risk-Reward Ratio'].mean() if 'Risk-Reward Ratio' in df else 0
    
    # Cumulative Drawdown Calculation
    df_sorted = df.sort_values(by='Date of Exit').copy()
    df_sorted['Cumulative_PnL'] = df_sorted['Profit or Loss'].cumsum()
    df_sorted['Peak'] = df_sorted['Cumulative_PnL'].cummax()
    df_sorted['Drawdown'] = df_sorted['Cumulative_PnL'] - df_sorted['Peak']
    max_drawdown = df_sorted['Drawdown'].min() if not df_sorted.empty else 0

    return {
        "Total Trades": total_trades,
        "Win Rate (%)": f"{win_rate:.1f}%",
        "Net P&L": f"{net_pnl:,.2f}",
        "Avg Gain": f"{avg_gain:,.2f}",
        "Avg Loss": f"{avg_loss:,.2f}",
        "Avg R:R": f"{avg_rr:.2f}",
        "Largest Win": f"{largest_win:,.2f}",
        "Largest Loss": f"{largest_loss:,.2f}",
        "Max Drawdown": f"{max_drawdown:,.2f}"
    }

# ==================== APP LAYOUT & NAVIGATION ==================== #

st.title("📈 Swing Trading Journal & Analytics Dashboard")
df = load_data()

tabs = st.tabs([
    "📊 Dashboard & Performance", 
    "🔍 Trade Inspector & Charts", 
    "➕ Log New Trade", 
    "✏️ Edit / Delete Trades", 
    "📁 Raw Journal Data"
])

# ==================== TAB 1: DASHBOARD ==================== #
with tabs[0]:
    st.subheader("Summary Performance Metrics")
    metrics = calculate_metrics(df)
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Trades", metrics["Total Trades"])
    m_col2.metric("Win Rate", metrics["Win Rate (%)"])
    m_col3.metric("Net Profit / Loss", metrics["Net P&L"])
    m_col4.metric("Avg Risk-Reward Ratio", metrics["Avg R:R"])
    
    m_col5, m_col6, m_col7, m_col8 = st.columns(4)
    m_col5.metric("Average Gain", metrics["Avg Gain"])
    m_col6.metric("Average Loss", metrics["Avg Loss"])
    m_col7.metric("Largest Win / Loss", f"{metrics['Largest Win']} / {metrics['Largest Loss']}")
    m_col8.metric("Max Drawdown", metrics["Max Drawdown"])

    st.markdown("---")
    
    if not df.empty:
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("Cumulative P&L Curve")
            df_chart = df.sort_values(by="Date of Exit").copy()
            df_chart["Equity Curve"] = df_chart["Profit or Loss"].cumsum()
            fig_pnl = px.line(df_chart, x="Date of Exit", y="Equity Curve", markers=True, 
                              title="Equity Growth Over Time", labels={"Equity Curve": "Cumulative P&L"})
            fig_pnl.add_hline(y=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig_pnl, use_container_width=True)
            
        with g2:
            st.subheader("Win / Loss Ratio")
            fig_pie = px.pie(df, names="Trade Outcome", title="Trade Outcomes Breakdown",
                             color="Trade Outcome",
                             color_discrete_map={"Win": "#2ecc71", "Loss": "#e74c3c", "Break-even": "#f1c40f"})
            st.plotly_chart(fig_pie, use_container_width=True)
            
        g3, g4 = st.columns(2)
        
        with g3:
            st.subheader("Performance by Strategy")
            fig_strat = px.bar(df, x="Trading Strategy Used", y="Profit or Loss", color="Trade Outcome",
                               title="P&L Generated by Strategy", barmode="group")
            st.plotly_chart(fig_strat, use_container_width=True)
            
        with g4:
            st.subheader("Emotional Mindset Impact")
            fig_emo = px.box(df, x="How Did You Feel", y="Profit or Loss", points="all",
                             title="P&L Distribution by Emotional State")
            st.plotly_chart(fig_emo, use_container_width=True)
    else:
        st.info("No trades logged yet. Start by adding a trade in the 'Log New Trade' tab.")

# ==================== TAB 2: TRADE INSPECTOR & CHARTS ==================== #
with tabs[1]:
    st.subheader("🔍 Detailed Trade Inspector & Chart Gallery")
    
    if df.empty:
        st.info("No trades logged yet to inspect.")
    else:
        # Trade Selection Menu
        trade_list = [f"Trade #{row['Trade Number']} - {row['Scrip Name']} ({row['Trade Outcome']})" for _, row in df.iterrows()]
        selected_trade_str = st.selectbox("Select Trade to Inspect", trade_list)
        
        # Extract Trade Number
        selected_trade_no = int(selected_trade_str.split("#")[1].split(" ")[0])
        trade_data = df[df["Trade Number"] == selected_trade_no].iloc[0]
        
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            st.markdown(f"### Trade #{trade_data['Trade Number']}: {trade_data['Scrip Name']}")
            
            pnl_color = "green" if trade_data['Profit or Loss'] > 0 else ("red" if trade_data['Profit or Loss'] < 0 else "gray")
            st.markdown(f"**Outcome:** :{pnl_color}[{trade_data['Trade Outcome']} ({trade_data['Profit or Loss']:,.2f})]")
            
            i1, i2, i3 = st.columns(3)
            i1.write(f"**Entry Date:** {trade_data['Date of Entry']}")
            i2.write(f"**Exit Date:** {trade_data['Date of Exit']}")
            i3.write(f"**Holding Days:** {trade_data['Holding Days']}")
            
            i4, i5, i6 = st.columns(3)
            i4.write(f"**Position:** {trade_data['Position Type']}")
            i5.write(f"**Entry Price:** {trade_data['Entry Price']}")
            i6.write(f"**Exit Price:** {trade_data['Exit Price']}")

            i7, i8, i9 = st.columns(3)
            i7.write(f"**Strategy:** {trade_data['Trading Strategy Used']}")
            i8.write(f"**Risk-Reward:** {trade_data['Risk-Reward Ratio']}")
            i9.write(f"**Emotion:** {trade_data['How Did You Feel']}")

            st.markdown("---")
            st.markdown(f"**Trade Rationale:**\n{trade_data['Reason for Entering']}")
            st.markdown(f"**Technical Setup:**\n{trade_data['Technical Setup']}")
            st.markdown(f"**Key Takeaways:**\n{trade_data['Key Takeaways']}")
            
        with c_right:
            st.markdown("### 📊 Trade Technical Chart")
            chart_path = str(trade_data.get('Chart Path', ''))
            
            if chart_path and os.path.exists(chart_path):
                image = Image.open(chart_path)
                st.image(image, caption=f"Chart Screenshot for Trade #{selected_trade_no} ({trade_data['Scrip Name']})", use_container_width=True)
            else:
                st.warning("No chart image uploaded or found for this trade.")

# ==================== TAB 3: LOG NEW TRADE ==================== #
with tabs[2]:
    st.subheader("Log a New Swing Trade")
    
    next_trade_no = int(df["Trade Number"].max() + 1) if not df.empty else 1
    
    with st.form("add_trade_form", clear_on_submit=True):
        st.markdown("### 1. Trade Details")
        c1, c2, c3, c4 = st.columns(4)
        trade_num = c1.number_input("Trade Number", value=next_trade_no, step=1)
        scrip = c2.text_input("Scrip / Symbol Name", value="").upper()
        pos_type = c3.selectbox("Position Type", ["Long", "Short"])
        duration = c4.selectbox("Trade Duration", ["Swing", "Intraday", "Position"])
        
        c5, c6, c7, c8 = st.columns(4)
        date_entry = c5.date_input("Date of Entry", value=date.today())
        date_exit = c6.date_input("Date of Exit", value=date.today())
        tot_cap = c7.number_input("Total Capital", min_value=0.0, value=100000.0, step=1000.0)
        cap_dep = c8.number_input("Capital Deployed", min_value=0.0, value=20000.0, step=1000.0)
        
        c9, c10, c11, c12 = st.columns(4)
        qty = c9.number_input("Position Size / Quantity", min_value=1, value=10)
        entry_p = c10.number_input("Entry Price", min_value=0.0, value=100.0, step=0.1)
        exit_p = c11.number_input("Exit Price", min_value=0.0, value=110.0, step=0.1)
        sl_price = c12.number_input("Stop Loss Level", min_value=0.0, value=95.0, step=0.1)
        
        c13, c14, c15 = st.columns(3)
        trail_sl = c13.number_input("Trail SL Level", min_value=0.0, value=98.0, step=0.1)
        rr_ratio = c14.number_input("Risk-Reward Ratio", min_value=0.0, value=2.0, step=0.1)
        strategy = c15.selectbox("Trading Strategy Used", ["Breakout", "Mean Reversion", "Trend Following", "Pullback", "Other"])

        st.markdown("### 2. Trade Rationale & Chart Upload")
        r1, r2 = st.columns(2)
        reason = r1.text_area("Reason for Entering the Trade")
        tech_setup = r2.text_area("Technical Setup (Patterns, Support/Resistance, Indicators)")
        
        # File Uploader for Technical Chart
        uploaded_chart = st.file_uploader("Upload Technical Chart Image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
        
        r3, r4 = st.columns(2)
        fund_factors = r3.text_area("Fundamental Factors (Earnings, News, Macro)")
        mkt_cond = r4.selectbox("Market Conditions", ["Trending Up", "Trending Down", "Range-bound", "High Volatility"])

        st.markdown("### 3. Trade Management")
        m1, m2, m3 = st.columns(3)
        sl_adj = m1.text_area("Stop Loss Adjustments")
        tp_adj = m2.text_area("Take Profit Adjustments")
        partial_exit = m3.text_area("Partial Exit Details")

        st.markdown("### 4. Emotional Reflection")
        e1, e2, e3 = st.columns(3)
        emotion = e1.selectbox("How Did You Feel?", ["Calm", "Anxious", "Confident", "Fearful", "Greedy"])
        stick_plan = e2.selectbox("Did You Stick to Your Plan?", ["Yes", "No"])
        triggers = e3.text_input("Emotional Triggers (FOMO, Impatience, Greed, etc.)")
        notes_psych = st.text_area("Decision-Making & Psychological Notes")

        st.markdown("### 5. Post-Trade Analysis")
        p1, p2, p3 = st.columns(3)
        
        # Automatic P&L & Holding calculation
        calc_holding = (date_exit - date_entry).days
        pnl_val = (exit_p - entry_p) * qty if pos_type == "Long" else (entry_p - exit_p) * qty
        outcome_val = "Win" if pnl_val > 0 else ("Loss" if pnl_val < 0 else "Break-even")
        
        pnl = p1.number_input("Profit or Loss (Auto-Calculated default)", value=float(pnl_val))
        outcome = p2.selectbox("Trade Outcome", ["Win", "Loss", "Break-even"], index=["Win", "Loss", "Break-even"].index(outcome_val))
        reason_sf = p3.text_area("Reason for Success or Failure")
        
        a1, a2 = st.columns(2)
        takeaways = a1.text_area("Key Takeaways")
        improvements = a2.text_area("Improvement Areas")

        submit = st.form_submit_button("💾 Save Trade to Journal")
        
        if submit:
            # Handle Chart Saving
            saved_chart_path = save_chart_image(uploaded_chart, trade_num)
            
            new_entry = {
                "Trade Number": trade_num, "Date of Entry": date_entry, "Date of Exit": date_exit,
                "Holding Days": calc_holding, "Total Capital": tot_cap, "Capital Deployed": cap_dep,
                "Scrip Name": scrip, "Position Type": pos_type, "Position Size/Quantity": qty,
                "Entry Price": entry_p, "Exit Price": exit_p, "Stop Loss Level": sl_price,
                "Trail SL Level": trail_sl, "Risk-Reward Ratio": rr_ratio, "Trade Duration": duration,
                "Trading Strategy Used": strategy, "Reason for Entering": reason,
                "Technical Setup": tech_setup, "Fundamental Factors": fund_factors,
                "Market Conditions": mkt_cond, "Stop Loss Adjustment": sl_adj,
                "Take Profit Adjustment": tp_adj, "Partial Exit": partial_exit,
                "How Did You Feel": emotion, "Stick to Plan": stick_plan,
                "Emotional Triggers": triggers, "Decision-Making Notes": notes_psych,
                "Profit or Loss": pnl, "Trade Outcome": outcome,
                "Reason for Success/Failure": reason_sf, "Key Takeaways": takeaways,
                "Improvement Areas": improvements, "Chart Path": saved_chart_path
            }
            
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)
            st.success(f"Trade #{trade_num} for {scrip} saved successfully!")
            st.rerun()

# ==================== TAB 4: EDIT / DELETE ==================== #
with tabs[3]:
    st.subheader("Manage Existing Trades")
    
    if df.empty:
        st.info("No trades to manage.")
    else:
        selected_trade_no = st.selectbox("Select Trade Number to Modify / Delete", df["Trade Number"].tolist())
        trade_idx = df[df["Trade Number"] == selected_trade_no].index[0]
        
        col_del, col_chart_up = st.columns([1, 2])
        
        with col_del:
            if st.button("❌ Delete Selected Trade", type="primary"):
                # Clean up associated chart image if present
                old_chart = df.loc[trade_idx, "Chart Path"]
                if old_chart and os.path.exists(str(old_chart)):
                    os.remove(str(old_chart))
                    
                df = df.drop(trade_idx).reset_index(drop=True)
                save_data(df)
                st.success(f"Trade #{selected_trade_no} deleted.")
                st.rerun()

        with col_chart_up:
            replacement_chart = st.file_uploader("Replace/Upload Chart Image for this Trade", type=["png", "jpg", "jpeg"], key="edit_chart_uploader")
            if st.button("🖼️ Update Chart Image"):
                if replacement_chart is not None:
                    new_path = save_chart_image(replacement_chart, selected_trade_no)
                    df.loc[trade_idx, "Chart Path"] = new_path
                    save_data(df)
                    st.success(f"Chart image updated for Trade #{selected_trade_no}!")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Edit Trade Data Attributes")
        
        edited_df = st.data_editor(df[df["Trade Number"] == selected_trade_no], key="edit_grid")
        if st.button("💾 Save Text Data Modifications"):
            df.iloc[trade_idx] = edited_df.iloc[0]
            save_data(df)
            st.success(f"Trade #{selected_trade_no} updated successfully.")
            st.rerun()

# ==================== TAB 5: RAW DATA ==================== #
with tabs[4]:
    st.subheader("All Journal Entries (Synced with Excel)")
    st.dataframe(df, use_container_width=True)
    
    if os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, "rb") as f:
            st.download_button(
                label="📥 Download Excel File",
                data=f,
                file_name=EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )