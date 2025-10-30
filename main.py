import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import psutil
import time

# --- 🌙 Dark Theme Settings ---
st.set_page_config(page_title="System Monitor Dashboard", layout="wide")

# Custom CSS for a dark sleek look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stSidebar {
        background-color: #111827;
    }
    h1, h2, h3, h4 {
        color: #00b4d8;
    }
    .stDataFrame {
        background-color: #111;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🧭 Sidebar Navigation ---
st.sidebar.title("🧠 System Dashboard")
page = st.sidebar.radio("Navigate", [
    "📊 Real-Time Monitor",
    "📁 CSV Log Viewer",
    "📈 Historical Graphs",
    "⚖️ Comparison Mode",
    "ℹ️ About"
])

# --- 🔍 Helper function to read system stats ---
def get_syscalls_and_context_switches():
    syscalls = ctxt = 0
    with open("/proc/stat", "r") as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith("processes "):
            syscalls = int(line.split()[1])
        elif line.startswith("ctxt "):
            ctxt = int(line.split()[1])
    return syscalls, ctxt

# --- 🟢 Page 1: Real-Time Monitor ---
if page == "📊 Real-Time Monitor":
    st.title("📊 Real-Time System Monitoring")
    st.write("⚙️ Live CPU, Syscalls, and Context Switches updating every 2 seconds.")

    # Live metrics
    cpu_placeholder = st.empty()
    syscall_placeholder = st.empty()
    ctxt_placeholder = st.empty()
    chart_placeholder = st.empty()

    cpu_values = []
    syscall_values = []
    ctxt_values = []

    prev_syscalls, prev_ctxt = get_syscalls_and_context_switches()

    # Streamlit stop condition
    run = st.checkbox("▶️ Start Monitoring", value=False)

    while run:
        cpu_usage = psutil.cpu_percent(interval=1)
        syscalls, ctxt = get_syscalls_and_context_switches()

        delta_syscalls = syscalls - prev_syscalls
        delta_ctxt = ctxt - prev_ctxt
        prev_syscalls, prev_ctxt = syscalls, ctxt

        cpu_values.append(cpu_usage)
        syscall_values.append(delta_syscalls)
        ctxt_values.append(delta_ctxt)

        # Display metrics dynamically
        cpu_placeholder.metric("🧠 CPU Usage (%)", f"{cpu_usage:.2f}")
        syscall_placeholder.metric("📞 Syscalls/sec", f"{delta_syscalls}")
        ctxt_placeholder.metric("🔁 Context Switches/sec", f"{delta_ctxt}")

        # Real-time line chart
        df_live = pd.DataFrame({
            "CPU (%)": cpu_values,
            "Syscalls/sec": syscall_values,
            "Context Switches/sec": ctxt_values
        })
        chart_placeholder.line_chart(df_live)

        time.sleep(2)

# --- 📁 Page 2: CSV Log Viewer ---
elif page == "📁 CSV Log Viewer":
    st.title("📁 System Log Viewer")

    log_path = "system_monitor_log.csv"
    df = None

    if os.path.exists(log_path):
        st.success(f"✅ Automatically loaded: {log_path}")
        df = pd.read_csv(log_path)
    else:
        st.warning("⚠️ Log file not found. Please upload a CSV manually.")
        uploaded = st.file_uploader("Upload your system_monitor_log.csv file", type=["csv"])
        if uploaded:
            df = pd.read_csv(uploaded)
            st.success("✅ File uploaded successfully!")

    if df is not None:
        st.dataframe(df, use_container_width=True)
        if st.button("📊 Show Basic Stats"):
            st.write(df.describe())

# --- 📈 Page 3: Historical Graphs ---
elif page == "📈 Historical Graphs":
    st.title("📈 Historical Data Visualization")

    log_path = "system_monitor_log.csv"
    if os.path.exists(log_path):
        df = pd.read_csv(log_path)
        st.success(f"✅ Loaded: {log_path}")

        # Only numeric columns
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if numeric_cols:
            selected_metric = st.selectbox("Select a metric to visualize:", numeric_cols)

            # Create figure
            fig, ax = plt.subplots(figsize=(10, 5))
            y = df[selected_metric]
            x = range(len(y))

            # Plot main line
            ax.plot(x, y, color="#00b4d8", linewidth=2, label=selected_metric)

            # Highlight max and min points
            max_idx = y.idxmax()
            min_idx = y.idxmin()
            ax.scatter(max_idx, y[max_idx], color='red', s=100, label=f"Max: {y[max_idx]:.2f}")
            ax.scatter(min_idx, y[min_idx], color='lime', s=100, label=f"Min: {y[min_idx]:.2f}")

            # Axis labels and title
            ax.set_xlabel("Time / Index", color='white', fontsize=12)
            ax.set_ylabel(selected_metric, color='white', fontsize=12)
            ax.set_title(f"{selected_metric} Trend with Highlighted Extremes", color='#00b4d8', fontsize=14)

            # Dark background styling
            ax.set_facecolor('#111827')
            fig.patch.set_facecolor('#0e1117')
            ax.tick_params(colors='white')

            # Show legend
            ax.legend(facecolor="#111827", labelcolor='white')

            # Show plot in Streamlit
            st.pyplot(fig)

            # Info panel below chart
            st.markdown(f"""
                **📊 Metric:** `{selected_metric}`  
                **🔴 Max Value:** {y[max_idx]:.2f} (at index {max_idx})  
                **🟢 Min Value:** {y[min_idx]:.2f} (at index {min_idx})  
            """)
        else:
            st.warning("⚠️ No numeric columns found in CSV.")
    else:
        st.warning("⚠️ No system_monitor_log.csv found. Please upload in the Log Viewer section.")

# --- ⚖️ Page 4: Comparison Mode ---
elif page == "⚖️ Comparison Mode":
    st.title("⚖️ Compare eBPF vs Baseline Models")
    st.write("Upload two CSV files to visualize performance differences.")

    col1, col2 = st.columns(2)
    with col1:
        file1 = st.file_uploader("Upload eBPF CSV", type=["csv"], key="ebpf")
    with col2:
        file2 = st.file_uploader("Upload Baseline CSV", type=["csv"], key="baseline")

    if file1 and file2:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        st.success("✅ Both files loaded successfully!")

        st.write("### 🔍 Average Comparison")
        metrics = ["cpu_percent", "Energy_estimate"]

        for m in metrics:
            if m in df1.columns and m in df2.columns:
                avg1 = df1[m].mean()
                avg2 = df2[m].mean()
                st.write(f"**{m}** → eBPF: {avg1:.2f} | Baseline: {avg2:.2f} | Δ = {avg1 - avg2:+.2f}")

# --- ℹ️ Page 5: About ---
elif page == "ℹ️ About":
    st.title("ℹ️ About Project")
    st.write("""
        ### 🧠 Energy-Aware eBPF System Monitor
        **Features:**
        - Tracks CPU, Syscalls, Context Switches, and Energy
        - Combines Kernel (eBPF) + User-Space (psutil) Data
        - Supports CSV Log Viewing & Historical Analysis  
        - Comparison Mode: eBPF vs Baseline  
        
        **Developed by:** *Anmol Kumari*  
        **Theme:** Dark / Modern Adaptive
    """)
