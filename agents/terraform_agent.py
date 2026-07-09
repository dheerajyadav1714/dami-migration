# agents/terraform_agent.py
import os
import io
import zipfile
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

class TerraformAgent:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
        
    def generate_landing_zone_zip(self, target_cloud="Google Cloud Platform (GCP)") -> bytes:
        """
        Generates Landing Zone Terraform configurations (vpc.tf, subnets.tf, firewall.tf)
        based on the detected environments and returns a zip file in memory.
        """
        client = bigquery.Client(project=self.project_id)
        
        # Determine environments to map subnets
        envs = ["prod", "dev", "staging"]
        try:
            query = f"SELECT DISTINCT environment FROM `{self.project_id}.{self.dataset}.servers` WHERE environment IS NOT NULL"
            df = client.query(query).to_dataframe()
            if not df.empty:
                envs = df['environment'].str.lower().tolist()
        except Exception as e:
            print(f"Fallback to default environments due to: {e}")
            
        tf_files = {}
        
        if "AWS" in target_cloud:
            tf_files["provider.tf"] = 'provider "aws" {\n  region = "us-east-1"\n}'
            tf_files["vpc.tf"] = 'resource "aws_vpc" "landing_zone" {\n  cidr_block = "10.0.0.0/16"\n  enable_dns_hostnames = true\n  tags = { Name = "DAMI-Landing-Zone" }\n}'
            
            subnets_hcl = ""
            for idx, env in enumerate(envs):
                cidr = f"10.0.{idx}.0/24"
                subnets_hcl += f'resource "aws_subnet" "{env}_subnet" {{\n  vpc_id = aws_vpc.landing_zone.id\n  cidr_block = "{cidr}"\n  tags = {{ Name = "{env}-subnet" }}\n}}\n\n'
            tf_files["subnets.tf"] = subnets_hcl
            
            tf_files["security_groups.tf"] = 'resource "aws_security_group" "allow_web" {\n  name = "allow_web"\n  vpc_id = aws_vpc.landing_zone.id\n  ingress {\n    from_port = 80\n    to_port = 80\n    protocol = "tcp"\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}'
            
        elif "Azure" in target_cloud:
            tf_files["provider.tf"] = 'provider "azurerm" {\n  features {}\n}'
            tf_files["vnet.tf"] = 'resource "azurerm_resource_group" "rg" {\n  name = "DAMI-LandingZone-RG"\n  location = "East US"\n}\n\nresource "azurerm_virtual_network" "vnet" {\n  name = "dami-vnet"\n  address_space = ["10.0.0.0/16"]\n  location = azurerm_resource_group.rg.location\n  resource_group_name = azurerm_resource_group.rg.name\n}'
            
            subnets_hcl = ""
            for idx, env in enumerate(envs):
                cidr = f"10.0.{idx}.0/24"
                subnets_hcl += f'resource "azurerm_subnet" "{env}_subnet" {{\n  name = "{env}-subnet"\n  resource_group_name = azurerm_resource_group.rg.name\n  virtual_network_name = azurerm_virtual_network.vnet.name\n  address_prefixes = ["{cidr}"]\n}}\n\n'
            tf_files["subnets.tf"] = subnets_hcl
            
        else:
            # GCP Default
            tf_files["provider.tf"] = 'provider "google" {\n  project = var.project_id\n  region  = "us-central1"\n}'
            tf_files["vpc.tf"] = 'resource "google_compute_network" "landing_zone" {\n  name                    = "dami-landing-zone"\n  auto_create_subnetworks = false\n}'
            
            subnets_hcl = ""
            for idx, env in enumerate(envs):
                cidr = f"10.{idx}.0.0/24"
                subnets_hcl += f'resource "google_compute_subnetwork" "{env}_subnet" {{\n  name          = "{env}-subnet"\n  ip_cidr_range = "{cidr}"\n  region        = "us-central1"\n  network       = google_compute_network.landing_zone.id\n}}\n\n'
            tf_files["subnets.tf"] = subnets_hcl
            
            tf_files["firewall.tf"] = 'resource "google_compute_firewall" "allow-internal" {\n  name    = "dami-allow-internal"\n  network = google_compute_network.landing_zone.name\n  allow {\n    protocol = "tcp"\n    ports    = ["0-65535"]\n  }\n  allow {\n    protocol = "udp"\n    ports    = ["0-65535"]\n  }\n  allow {\n    protocol = "icmp"\n  }\n  source_ranges = ["10.0.0.0/8"]\n}'
            
        # Create Zip in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_name, file_content in tf_files.items():
                zip_file.writestr(file_name, file_content)
                
        return zip_buffer.getvalue()
