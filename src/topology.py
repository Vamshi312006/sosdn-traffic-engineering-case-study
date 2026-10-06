"""
Topology Module for SOSDN Simulation
Builds the 16-switch network topology with 6 SOA servers and 50 user access ports.
Reference: Beshley et al., JCN 2024, Section VII, Fig. 9(b).
"""

import networkx as nx
from typing import Dict, List, Tuple, Any

class SOSDNTopology:
    """
    Constructs and manages the 16-switch SOSDN graph.
    - 4 Core Switches: SW1, SW2, SW3, SW4 in a full mesh (K4).
    - 12 Edge Switches: 3 per core switch (SW1_E1..E3, SW2_E1..E3, etc.).
    - 6 SOA Servers deployed on edge switches.
    - 50 User access endpoints distributed across edge switches.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.graph = nx.DiGraph()  # Directed graph as per paper: w(i,j) != w(j,i)
        self.core_switches = config['topology']['core_switches']
        self.edge_switches_per_core = config['topology']['edge_switches_per_core']
        self.link_bw = config['topology']['link_bandwidth_mbps']
        self.core_delay = config['topology']['core_link_delay_ms']
        self.edge_delay = config['topology']['edge_link_delay_ms']
        self.buffer_size = config['topology']['buffer_size_packets']
        
        self.server_nodes: Dict[str, Dict[str, Any]] = {}
        self.user_nodes: Dict[int, str] = {}  # user_id -> edge_switch
        
        self._build_topology()
        self._attach_servers()
        self._distribute_users()

    def _build_topology(self):
        """Construct the core mesh and hierarchical edge links."""
        # 1. Add 4 Core switches
        for sw in self.core_switches:
            self.graph.add_node(sw, type='core_switch')

        # 2. Connect Core switches in full mesh (K4 clique)
        for i in range(len(self.core_switches)):
            for j in range(len(self.core_switches)):
                if i != j:
                    u, v = self.core_switches[i], self.core_switches[j]
                    self.graph.add_edge(
                        u, v,
                        capacity_mbps=self.link_bw,
                        base_delay_ms=self.core_delay,
                        current_load_mbps=0.0,
                        packet_loss_percent=0.0,
                        delay_ms=self.core_delay,
                        jitter_ms=1.0,
                        available_bw_mbps=self.link_bw,
                        buffer_size=self.buffer_size,
                        queue_packets=0,
                        type='core_link'
                    )

        # 3. Add Edge switches and connect to respective core switch
        for core in self.core_switches:
            for e_idx in range(1, self.edge_switches_per_core + 1):
                edge_name = f"{core}_E{e_idx}"
                self.graph.add_node(edge_name, type='edge_switch', parent_core=core)
                
                # Bidirectional link between core and edge
                for u, v in [(core, edge_name), (edge_name, core)]:
                    self.graph.add_edge(
                        u, v,
                        capacity_mbps=self.link_bw,
                        base_delay_ms=self.edge_delay,
                        current_load_mbps=0.0,
                        packet_loss_percent=0.0,
                        delay_ms=self.edge_delay,
                        jitter_ms=0.5,
                        available_bw_mbps=self.link_bw,
                        buffer_size=self.buffer_size,
                        queue_packets=0,
                        type='edge_link'
                    )

    def _attach_servers(self):
        """Deploy 6 SOA service servers on specific edge switches as depicted in Fig. 9(b)."""
        server_configs = self.config['servers']['instances']
        for s_cfg in server_configs:
            sid = s_cfg['id']
            switch = s_cfg['switch']
            self.server_nodes[sid] = {
                'id': sid,
                'type': s_cfg['type'],
                'switch': switch,
                'cpu_load': s_cfg['base_cpu_load'],
                'ram_load': s_cfg['base_ram_load'],
                'proc_time_ms': s_cfg['base_proc_time_ms'],
                'loss_prob': s_cfg['base_loss_prob'],
                'nic_load': s_cfg['base_nic_load'],
                'active_requests': 0
            }

    def _distribute_users(self):
        """
        Distribute users across edge switches.
        User 7 is placed specifically on SW4_E1 (across the SW4-SW1 bottleneck from IPTV Server 1/2 on SW1).
        Users 1 to 10 are the 10 IPTV SLA users distributed across SW1, SW2, SW3, and SW4 clusters.
        """
        edge_switches = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'edge_switch']
        total_users = self.config['users']['total_users']
        
        # User 7 specifically on SW4_E1 (traversing the congested core link in baseline)
        self.user_nodes[7] = "SW4_E1"

        # Dedicated distribution for the 10 IPTV users (Users 1-10) to match Fig. 10:
        # Users 1, 3, 5 are local or nearby (SW1_E1, SW1_E3, SW2_E1) -> Green
        # Users 2, 4, 6, 8, 9, 10 are on other switches -> Yellow
        iptv_placements = {
            1: "SW1_E3",  # Local to SW1 (Green)
            2: "SW2_E2",  # Yellow
            3: "SW1_E1",  # Local to SW1 (Green)
            4: "SW3_E2",  # Yellow
            5: "SW1_E2",  # Local to SW1 (Green)
            6: "SW2_E3",  # Yellow
            7: "SW4_E1",  # Directly across congested SW4-SW1 link (Red in baseline!)
            8: "SW3_E1",  # Yellow
            9: "SW2_E1",  # Yellow
            10: "SW3_E3"  # Yellow
        }

        for uid in range(1, total_users + 1):
            if uid in iptv_placements:
                self.user_nodes[uid] = iptv_placements[uid]
            else:
                assigned_edge = edge_switches[(uid - 1) % len(edge_switches)]
                self.user_nodes[uid] = assigned_edge

    def reset_link_loads(self):
        """Reset dynamic link counters before running an experiment iteration."""
        for u, v, d in self.graph.edges(data=True):
            d['current_load_mbps'] = 0.0
            d['packet_loss_percent'] = 0.0
            d['delay_ms'] = d['base_delay_ms']
            d['jitter_ms'] = 0.5
            d['available_bw_mbps'] = d['capacity_mbps']
            d['queue_packets'] = 0

    def get_server_location(self, server_id: str) -> str:
        """Return the switch to which a server is attached."""
        return self.server_nodes[server_id]['switch']

    def get_user_location(self, user_id: int) -> str:
        """Return the edge switch to which a user is attached."""
        return self.user_nodes[user_id]
