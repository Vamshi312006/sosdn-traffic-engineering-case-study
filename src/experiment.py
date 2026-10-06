"""
Experiment Runner Module
Executes experiments across scenarios, methods, and seeds, saving CSV results.
"""

import os
import yaml
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from .topology import SOSDNTopology
from .traffic import TrafficGenerator
from .monitoring import SOSDNMonitor
from .prioritization import AdaptivePrioritization
from .routing import MultiCriteriaRouter
from .server_selection import ServerSelector
from .qos_qoe import QoEEvaluator
from .baselines import MethodOrchestrator

def load_config(config_path: str = None) -> Dict[str, Any]:
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, 'config', 'experiment_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_experiment(config_path: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Runs the complete experiment matrix and returns raw and summary DataFrames."""
    config = load_config(config_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, config['general']['output_dir'], 'raw')
    proc_dir = os.path.join(base_dir, config['general']['output_dir'], 'processed')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)

    seeds = config['general']['random_seeds']
    scenarios = config['scenarios']
    methods = config['methods']
    
    qoe_eval = QoEEvaluator(config)
    raw_records = []

    print(f"=== Starting SOSDN Experiment Suite ===")
    print(f"Scenarios: {list(scenarios.keys())}")
    print(f"Methods: {[m['id'] for m in methods]}")
    print(f"Seeds: {seeds}")

    for sc_key, sc_val in scenarios.items():
        print(f"\n---> Running Scenario: {sc_val['label']} ({sc_key})")
        
        for method_info in methods:
            m_id = method_info['id']
            m_name = method_info['name']
            
            for seed in seeds:
                # 1. Initialize fresh topology
                topology = SOSDNTopology(config)
                traffic_gen = TrafficGenerator(config, topology)
                monitor = SOSDNMonitor(config, topology)
                prioritizer = AdaptivePrioritization(config)
                router = MultiCriteriaRouter(config, topology)
                server_selector = ServerSelector(config, topology)

                # 2. Get scaled flow demands
                rate_mult = sc_val.get('user_rate_multiplier', 1.0)
                flows = traffic_gen.get_flows(rate_multiplier=rate_mult)

                # 3. Inject background traffic
                traffic_gen.inject_background_traffic(sc_key, seed)

                # 4. Instantiate orchestrator and execute
                orchestrator = MethodOrchestrator(
                    method_cfg=method_info,
                    topology=topology,
                    router=router,
                    prioritizer=prioritizer,
                    server_selector=server_selector,
                    monitor=monitor
                )

                flow_telemetry = orchestrator.execute_method(flows, scenario_name=sc_key, seed=seed)

                # 5. Evaluate QoS/QoE for each flow
                for item in flow_telemetry:
                    eval_res = qoe_eval.evaluate_live_video_qoe(
                        loss_pct=item['loss_percent'],
                        delay_ms=item['delay_ms'],
                        jitter_ms=item['jitter_ms'],
                        bw_mbps=item['available_bw_mbps'],
                        path_cost=item['path_cost']
                    )

                    record = {
                        'scenario': sc_key,
                        'scenario_label': sc_val['label'],
                        'method_id': m_id,
                        'method_name': m_name,
                        'seed': seed,
                        'flow_id': item['flow_id'],
                        'user_id': item['user_id'],
                        'service_type': item['service_type'],
                        'service_class': item['service_class'],
                        'category': item['category'],
                        'priority': item['priority'],
                        'selected_server': item['selected_server'],
                        'path_hops': item['path_hops'],
                        'path_cost': item['path_cost'],
                        'loss_percent': item['loss_percent'],
                        'delay_ms': item['delay_ms'],
                        'jitter_ms': item['jitter_ms'],
                        'bandwidth_mbps': item['available_bw_mbps'],
                        'server_cpu': item['server_cpu'],
                        'server_ram': item['server_ram'],
                        'qos_x': eval_res['qos_x'],
                        'qoe_score': eval_res['qoe_score'],
                        'satisfaction': eval_res['satisfaction_category'],
                        'alert_color': eval_res['alert_color'],
                        'path_str': item['path_str']
                    }
                    raw_records.append(record)

    df_raw = pd.DataFrame(raw_records)
    raw_csv_path = os.path.join(raw_dir, 'results.csv')
    df_raw.to_csv(raw_csv_path, index=False)
    print(f"\n[OK] Raw results saved to: {raw_csv_path} ({len(df_raw)} records)")

    # 6. Generate Summary Statistics
    summary_cols = ['loss_percent', 'delay_ms', 'jitter_ms', 'bandwidth_mbps', 'qos_x', 'qoe_score', 'server_cpu']
    df_summary = df_raw.groupby(['scenario', 'method_id', 'method_name'])[summary_cols].agg(['mean', 'std']).reset_index()
    
    # Flatten multi-index columns
    df_summary.columns = [
        f"{c[0]}_{c[1]}" if c[1] else c[0] for c in df_summary.columns
    ]
    summary_csv_path = os.path.join(proc_dir, 'summary_metrics.csv')
    df_summary.to_csv(summary_csv_path, index=False)
    print(f"[OK] Summary results saved to: {summary_csv_path}")

    # Specific Target User 7 summary under High Congestion
    u7_df = df_raw[(df_raw['scenario'] == 'high_congestion') & (df_raw['user_id'] == 7)]
    u7_summary = u7_df.groupby(['method_id', 'method_name'])[['loss_percent', 'delay_ms', 'jitter_ms', 'qoe_score', 'alert_color']].agg({
        'loss_percent': 'mean',
        'delay_ms': 'mean',
        'jitter_ms': 'mean',
        'qoe_score': 'mean',
        'alert_color': lambda x: x.iloc[0]
    }).reset_index()
    u7_csv_path = os.path.join(proc_dir, 'user7_overload_summary.csv')
    u7_summary.to_csv(u7_csv_path, index=False)
    print(f"[OK] User 7 overload summary saved to: {u7_csv_path}")

    return df_raw, df_summary

if __name__ == '__main__':
    run_experiment()
