"""
PCAP Adapter for Network Traffic Data

This module provides an adapter for PCAP (Packet Capture) files containing network traffic data.
It normalizes the data into a standard format that can be used by our anomaly detection models.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
from .base_adapter import BaseAdapter
from utils.logger import get_logger

# Get logger
logger = get_logger()

class PCAPAdapter(BaseAdapter):
    """
    Adapter for PCAP files containing network traffic data.
    
    This adapter uses scapy to parse PCAP files and extract network traffic data.
    Note: This requires scapy to be installed (pip install scapy).
    """
    
    def __init__(self):
        """Initialize the PCAP adapter"""
        super().__init__()
        # Check if scapy is installed
        try:
            import scapy.all as scapy
            self.scapy = scapy
        except ImportError:
            logger.error("Scapy is required for PCAP adapter. Install with 'pip install scapy'")
            raise ImportError("Scapy is required for PCAP adapter")
    
    def load_data(self, source_path):
        """
        Load data from a PCAP file
        
        Args:
            source_path: Path to the PCAP file
            
        Returns:
            List of scapy packets
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"PCAP file not found: {source_path}")
        
        try:
            # Read the PCAP file
            packets = self.scapy.rdpcap(source_path)
            logger.info(f"Loaded PCAP file with {len(packets)} packets")
            return packets
        except Exception as e:
            logger.error(f"Error loading PCAP file: {str(e)}")
            raise
    
    def normalize(self, raw_data):
        """
        Normalize PCAP data into standard format
        
        Args:
            raw_data: List of scapy packets
            
        Returns:
            Pandas DataFrame with normalized data
        """
        packets = raw_data
        
        # Create empty lists for each column
        data = {
            'timestamp': [],
            'device_id': [],
            'src_ip': [],
            'dst_ip': [],
            'src_port': [],
            'dst_port': [],
            'protocol': [],
            'packet_size': [],
            'duration': [],
            'orig_bytes': [],
            'resp_bytes': []
        }
        
        # Process each packet
        for i, packet in enumerate(packets):
            # Extract IP layer if it exists
            if self.scapy.IP in packet:
                ip_layer = packet[self.scapy.IP]
                
                # Get timestamp
                timestamp = datetime.fromtimestamp(float(packet.time))
                
                # Get IP addresses
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                
                # Get protocol
                if self.scapy.TCP in packet:
                    protocol = 'tcp'
                    transport_layer = packet[self.scapy.TCP]
                    src_port = transport_layer.sport
                    dst_port = transport_layer.dport
                elif self.scapy.UDP in packet:
                    protocol = 'udp'
                    transport_layer = packet[self.scapy.UDP]
                    src_port = transport_layer.sport
                    dst_port = transport_layer.dport
                elif self.scapy.ICMP in packet:
                    protocol = 'icmp'
                    src_port = 0
                    dst_port = 0
                else:
                    protocol = str(ip_layer.proto)
                    src_port = 0
                    dst_port = 0
                
                # Get packet size
                packet_size = len(packet)
                
                # Add to data dictionary
                data['timestamp'].append(timestamp)
                data['device_id'].append(0)  # Default device ID
                data['src_ip'].append(src_ip)
                data['dst_ip'].append(dst_ip)
                data['src_port'].append(src_port)
                data['dst_port'].append(dst_port)
                data['protocol'].append(protocol)
                data['packet_size'].append(packet_size)
                data['duration'].append(0)  # Individual packets don't have duration
                data['orig_bytes'].append(packet_size)  # Use packet size as orig_bytes
                data['resp_bytes'].append(0)  # Can't determine response bytes from individual packets
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Aggregate packets into flows
        flows = self._aggregate_packets_to_flows(df)
        
        # Ensure all required columns exist
        flows = self.ensure_schema(flows)
        
        return flows
    
    def _aggregate_packets_to_flows(self, df):
        """
        Aggregate packets into flows based on 5-tuple
        
        Args:
            df: DataFrame with packet data
            
        Returns:
            DataFrame with flow data
        """
        # Create flow key (5-tuple)
        df['flow_key'] = df.apply(
            lambda x: f"{x['src_ip']}:{x['src_port']}-{x['dst_ip']}:{x['dst_port']}-{x['protocol']}",
            axis=1
        )
        
        # Group by flow key
        flow_groups = df.groupby('flow_key')
        
        # Aggregate data
        flows = flow_groups.agg({
            'timestamp': 'min',  # First packet time
            'device_id': 'first',  # Use first device ID
            'src_ip': 'first',
            'dst_ip': 'first',
            'src_port': 'first',
            'dst_port': 'first',
            'protocol': 'first',
            'packet_size': 'sum',  # Total bytes in flow
            'orig_bytes': 'sum',  # Total bytes from source
            'resp_bytes': 'sum'  # Total bytes from destination (always 0 in this case)
        }).reset_index()
        
        # Calculate duration as time between first and last packet in flow
        last_packet_times = flow_groups['timestamp'].max()
        flows['duration'] = (last_packet_times - flows['timestamp']).dt.total_seconds()
        
        # Remove flow_key column
        flows = flows.drop('flow_key', axis=1)
        
        return flows
