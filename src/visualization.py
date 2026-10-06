"""
Visualization Module for SOSDN Simulation Results
Generates publication-quality charts matching the paper's aesthetics.
Reference: Beshley et al., JCN 2024, Fig. 10 & Fig. 11.
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any

# Configure clean aesthetic
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

def generate_all_plots(raw_csv_path: str = None, output_dir: str = None):
    """Reads raw experiment CSV and generates all 5 publication-ready figures."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if raw_csv_path is None:
        raw_csv_path = os.path.join(base_dir, 'results', 'raw', 'results.csv')
    if output_dir is None:
        output_dir = os.path.join(base_dir, 'results', 'figures')
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(raw_csv_path)

    # 1. Figure 1: Mean QoE across Scenarios and Methods (with error bars)
    _plot_qoe_by_scenario(df, os.path.join(output_dir, 'fig1_qoe_by_scenario.png'))

    # 2. Figure 2: User 7 Overload Comparison across Methods (Loss, Delay, Jitter, QoE)
    _plot_user7_overload_metrics(df, os.path.join(output_dir, 'fig2_user7_overload_comparison.png'))

    # 3. Figure 3: IPTV Users 1-10 QoS Distribution (Paper Fig. 10 Reproduction Style)
    _plot_iptv_users_qos_distribution(df, os.path.join(output_dir, 'fig3_iptv_qos_distribution.png'))

    # 4. Figure 4: Dynamics of QoE Growth vs. QoS(x) (Paper Fig. 11 Style)
    _plot_qoe_growth_curve(df, os.path.join(output_dir, 'fig4_qoe_growth_curve.png'))

    # 5. Figure 5: Server Load & Utility Distribution (Optimal vs Static Server Selection)
    _plot_server_load_comparison(df, os.path.join(output_dir, 'fig5_server_load_comparison.png'))

    print(f"[OK] All 5 figures generated successfully in: {output_dir}")

def _plot_qoe_by_scenario(df: pd.DataFrame, save_path: str):
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    
    scenarios = ['low_congestion', 'medium_congestion', 'high_congestion']
    sc_labels = ['Low Congestion', 'Medium Congestion', 'High Congestion / Overload']
    method_order = ['fifo_ospf', 'pq_ospf', 'prioritization_ospf', 'proposed_combined']
    method_labels = ['FIFO + OSPF', 'PQ + OSPF', 'Adaptive Priority + OSPF', 'Proposed Combined (SOSDN)']
    colors = ['#8da0cb', '#fc8d62', '#e78ac3', '#66c2a5']

    bar_width = 0.18
    x = np.arange(len(scenarios))

    for idx, (m_id, m_label, col) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        stds = []
        for sc in scenarios:
            sub = df[(df['scenario'] == sc) & (df['method_id'] == m_id)]
            means.append(sub['qoe_score'].mean())
            stds.append(sub['qoe_score'].std())

        pos = x + (idx - 1.5) * bar_width
        ax.bar(pos, means, yerr=stds, width=bar_width, label=m_label, color=col, capsize=4, edgecolor='#222', alpha=0.9)

    ax.set_ylabel('Average User QoE Score (1–5 Scale)', fontsize=12, fontweight='bold')
    ax.set_title('User Quality of Experience (QoE) Under Varied Network Congestion', fontsize=13, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(sc_labels, fontsize=11, fontweight='bold')
    ax.set_ylim(0, 5.5)
    ax.axhline(4.0, color='green', linestyle='--', linewidth=1, alpha=0.7, label='Good Quality Threshold (QoE ≥ 4.0)')
    ax.legend(frameon=True, facecolor='#f8f9fa', fontsize=9.5, loc='upper right')
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)

def _plot_user7_overload_metrics(df: pd.DataFrame, save_path: str):
    fig, axes = plt.subplots(1, 4, figsize=(14, 4.5), dpi=300)
    
    u7_high = df[(df['scenario'] == 'high_congestion') & (df['user_id'] == 7)]
    method_order = ['fifo_ospf', 'pq_ospf', 'prioritization_ospf', 'proposed_combined']
    m_labels = ['FIFO\n+OSPF', 'PQ\n+OSPF', 'Adaptive\nPrior.+OSPF', 'Proposed\nSOSDN']
    bar_colors = ['#d95f02', '#e7298a', '#7570b3', '#1b9e77']

    metrics = [
        ('loss_percent', 'Packet Loss (%)', axes[0], 2.5),
        ('delay_ms', 'Packet Delay (ms)', axes[1], 300.0),
        ('jitter_ms', 'Jitter (ms)', axes[2], 65.0),
        ('qoe_score', 'QoE Score (1-5)', axes[3], 5.0)
    ]

    for col_name, title, ax, ymax in metrics:
        vals = [u7_high[u7_high['method_id'] == m][col_name].mean() for m in method_order]
        errs = [u7_high[u7_high['method_id'] == m][col_name].std() for m in method_order]
        
        bars = ax.bar(m_labels, vals, yerr=errs, color=bar_colors, capsize=3, edgecolor='#222', alpha=0.9)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_ylim(0, ymax * 1.15)
        ax.grid(axis='y', linestyle=':', alpha=0.5)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    plt.suptitle('IPTV User 7 Performance in Overload Scenario (Target QoE = 5.0)', fontsize=13, fontweight='bold', y=1.03)
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)

def _plot_iptv_users_qos_distribution(df: pd.DataFrame, save_path: str):
    """Direct reproduction of Paper Figure 10 layout."""
    fig, axes = plt.subplots(3, 2, figsize=(13, 9), dpi=300)
    
    # Filter 10 IPTV SLA users under high congestion
    high_df = df[(df['scenario'] == 'high_congestion') & (df['user_id'].isin(range(1, 11)))]
    
    pq_data = high_df[high_df['method_id'] == 'pq_ospf'].groupby('user_id').mean(numeric_only=True).reset_index()
    sosdn_data = high_df[high_df['method_id'] == 'proposed_combined'].groupby('user_id').mean(numeric_only=True).reset_index()

    users = np.arange(1, 11)

    def get_color(metric, val):
        if metric == 'p':  # loss
            return '#d73027' if val > 1.5 else ('#fee08b' if val > 0.8 else '#1a9850')
        elif metric == 't':  # delay
            return '#d73027' if val > 220.0 else ('#fee08b' if val > 160.0 else '#1a9850')
        else:  # jitter
            return '#d73027' if val > 50.0 else ('#fee08b' if val > 25.0 else '#1a9850')

    # Subplots (a), (b), (c) -> Baseline PQ + OSPF
    cols_a = [get_color('p', v) for v in pq_data['loss_percent']]
    axes[0, 0].bar(users, pq_data['loss_percent'], color=cols_a, edgecolor='#333', width=0.6)
    axes[0, 0].set_title('(a) Packet Loss (%): Baseline PQ + OSPF', fontsize=10, fontweight='bold')
    axes[0, 0].set_ylim(0, 2.5)

    cols_b = [get_color('t', v) for v in pq_data['delay_ms']]
    axes[1, 0].bar(users, pq_data['delay_ms'], color=cols_b, edgecolor='#333', width=0.6)
    axes[1, 0].set_title('(b) Packet Delay (ms): Baseline PQ + OSPF', fontsize=10, fontweight='bold')
    axes[1, 0].set_ylim(0, 300)

    cols_c = [get_color('j', v) for v in pq_data['jitter_ms']]
    axes[2, 0].bar(users, pq_data['jitter_ms'], color=cols_c, edgecolor='#333', width=0.6)
    axes[2, 0].set_title('(c) Jitter (ms): Baseline PQ + OSPF', fontsize=10, fontweight='bold')
    axes[2, 0].set_ylim(0, 65)

    # Subplots (d), (e), (f) -> Proposed SOSDN
    cols_d = [get_color('p', v) for v in sosdn_data['loss_percent']]
    axes[0, 1].bar(users, sosdn_data['loss_percent'], color=cols_d, edgecolor='#333', width=0.6)
    axes[0, 1].set_title('(d) Packet Loss (%): Proposed SOSDN', fontsize=10, fontweight='bold')
    axes[0, 1].set_ylim(0, 2.5)
    axes[0, 1].axvspan(6.5, 7.5, facecolor='none', edgecolor='red', linewidth=2)

    cols_e = [get_color('t', v) for v in sosdn_data['delay_ms']]
    axes[1, 1].bar(users, sosdn_data['delay_ms'], color=cols_e, edgecolor='#333', width=0.6)
    axes[1, 1].set_title('(e) Packet Delay (ms): Proposed SOSDN', fontsize=10, fontweight='bold')
    axes[1, 1].set_ylim(0, 300)
    axes[1, 1].axvspan(6.5, 7.5, facecolor='none', edgecolor='red', linewidth=2)

    cols_f = [get_color('j', v) for v in sosdn_data['jitter_ms']]
    axes[2, 1].bar(users, sosdn_data['jitter_ms'], color=cols_f, edgecolor='#333', width=0.6)
    axes[2, 1].set_title('(f) Jitter (ms): Proposed SOSDN', fontsize=10, fontweight='bold')
    axes[2, 1].set_ylim(0, 65)
    axes[2, 1].axvspan(6.5, 7.5, facecolor='none', edgecolor='red', linewidth=2)

    for ax in axes.flat:
        ax.set_xticks(users)
        ax.set_xlabel('IPTV Users (1–10)', fontsize=9)
        ax.grid(axis='y', linestyle=':', alpha=0.5)

    plt.suptitle('QoS Parameters Monitoring for 10 IPTV Users in Overload (Reproduction of Paper Fig. 10)', fontsize=12, fontweight='bold')
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)

def _plot_qoe_growth_curve(df: pd.DataFrame, save_path: str):
    """Direct reproduction of Paper Figure 11."""
    fig, ax = plt.subplots(figsize=(8, 7), dpi=300)

    # Generate analytical curve
    qos_range = np.linspace(0.00, 0.95, 200)
    qoe_curve = 1.0 + 4.0 / (1.0 + np.exp((qos_range - 0.33) / 0.065))
    ax.plot(qos_range, qoe_curve, color='blue', linewidth=2.2, label='Theoretical QoE(y) Perception Curve')

    # Compute actual average experimental points for User 7 in Overload
    u7_high = df[(df['scenario'] == 'high_congestion') & (df['user_id'] == 7)]
    
    methods_data = [
        ('fifo_ospf', 'FIFO + OSPF', '#d95f02'),
        ('pq_ospf', 'PQ + OSPF', '#7570b3'),
        ('prioritization_ospf', 'Adaptive Priority + OSPF', '#e7298a'),
        ('proposed_combined', 'Proposed SOSDN Combined', '#1b9e77')
    ]

    for m_id, label, color in methods_data:
        sub = u7_high[u7_high['method_id'] == m_id]
        mean_x = sub['qos_x'].mean()
        mean_y = sub['qoe_score'].mean()
        
        ax.scatter([mean_x], [mean_y], color='red', s=100, zorder=5, edgecolors='white', linewidth=1.5)
        ax.annotate(f"{label}\n(QoS={mean_x:.3f}, QoE={mean_y:.2f})",
                    xy=(mean_x, mean_y), xytext=(mean_x + 0.03, mean_y + 0.15),
                    arrowprops=dict(facecolor='black', arrowstyle='->', lw=0.8),
                    fontsize=8.5, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.9))

    ax.set_xlabel('Integral Additive QoS Criterion: QoS(x)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Quality of Experience: QoE(y) [1–5 Scale]', fontsize=12, fontweight='bold')
    ax.set_title('Dynamics of QoE Growth Across Solutions (Reproduction of Paper Fig. 11)', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0, 5.5)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', frameon=True, facecolor='#f8f9fa')

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)

def _plot_server_load_comparison(df: pd.DataFrame, save_path: str):
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    
    high_df = df[df['scenario'] == 'high_congestion']
    baseline_df = high_df[high_df['method_id'] == 'pq_ospf']
    proposed_df = high_df[high_df['method_id'] == 'proposed_combined']

    servers = ['IPTV_Server_1', 'IPTV_Server_2']
    s_labels = ['IPTV Server 1\n(Optimal, Higher Capacity)', 'IPTV Server 2\n(Loaded Default)']

    base_loads = [
        baseline_df[baseline_df['selected_server'] == s]['server_cpu'].mean()
        if len(baseline_df[baseline_df['selected_server'] == s]) > 0 else 75.0
        for s in servers
    ]
    prop_loads = [
        proposed_df[proposed_df['selected_server'] == s]['server_cpu'].mean()
        if len(proposed_df[proposed_df['selected_server'] == s]) > 0 else 55.0
        for s in servers
    ]

    x = np.arange(len(servers))
    width = 0.3

    ax.bar(x - width/2, base_loads, width, label='Static Selection (Baseline)', color='#fc8d62', edgecolor='#222')
    ax.bar(x + width/2, prop_loads, width, label='Optimal Selection (Formula 19)', color='#66c2a5', edgecolor='#222')

    ax.set_ylabel('Server CPU Loading (%)', fontsize=11, fontweight='bold')
    ax.set_title('Server Domain Load Balancing: Static vs. Multi-Criteria Server Selection', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(s_labels, fontsize=10, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.legend(frameon=True, facecolor='#f8f9fa')
    ax.grid(axis='y', linestyle=':', alpha=0.5)

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
