"""
Manual instruction generation for failed healing attempts
"""
from typing import Dict, Any, Optional
from pathlib import Path


def generate_manual_instructions(fault: Dict[str, Any], 
                                 analysis: Optional[Dict[str, Any]] = None,
                                 project_root: Optional[Path] = None) -> str:
    """Generate manual healing instructions when auto-healing fails
    
    Args:
        fault: Fault information dictionary
        analysis: Root cause analysis dictionary (optional)
        project_root: Project root path (optional, defaults to common path)
    
    Returns:
        Formatted manual instructions as string
    """
    fault_type = fault.get('type', 'unknown')
    service = fault.get('service', 'unknown')
    container_name = service if service.startswith('cloud-sim-') else f'cloud-sim-{service}'
    
    if project_root is None:
        # Default project root
        project_root = Path('/home/kasun/Documents/Heal-X-Bot')
    
    instructions = []
    instructions.append(f"# Manual Healing Instructions for {fault_type}")
    instructions.append("")
    instructions.append(f"**Fault:** {fault.get('message', 'Unknown fault')}")
    instructions.append(f"**Service:** {service}")
    instructions.append("")
    
    if fault_type == 'service_crash':
        instructions.append("## Steps to Fix Service Crash:")
        instructions.append("")
        instructions.append("1. **Check container status:**")
        instructions.append(f"   ```bash")
        instructions.append(f"   docker ps -a | grep {container_name}")
        instructions.append(f"   ```")
        instructions.append("")
        instructions.append("2. **View container logs:**")
        instructions.append(f"   ```bash")
        instructions.append(f"   docker logs {container_name} --tail 50")
        instructions.append(f"   ```")
        instructions.append("")
        instructions.append("3. **Restart the container:**")
        instructions.append(f"   ```bash")
        instructions.append(f"   docker restart {container_name}")
        instructions.append(f"   ```")
        instructions.append("")
        instructions.append("4. **If restart fails, recreate the container:**")
        instructions.append(f"   ```bash")
        instructions.append(f"   cd {project_root}")
        instructions.append(f"   # Try newer syntax first:")
        instructions.append(f"   docker compose -f config/docker-compose-cloud-sim.yml up -d --no-deps {service}")
        instructions.append(f"   # Or use older syntax:")
        instructions.append(f"   docker-compose -f config/docker-compose-cloud-sim.yml up -d --no-deps {service}")
        instructions.append(f"   ```")
    elif fault_type == 'cpu_exhaustion':
        instructions.append("## Steps to Fix CPU Exhaustion:")
        instructions.append("")
        instructions.append("1. **Identify CPU-intensive processes:**")
        instructions.append("   ```bash")
        instructions.append("   top -b -n 1 | head -20")
        instructions.append("   ```")
        instructions.append("")
        instructions.append("2. **Kill resource-hogging processes (if safe):**")
        instructions.append("   ```bash")
        instructions.append("   kill -9 <PID>")
        instructions.append("   ```")
        instructions.append("")
        instructions.append("3. **Clear system cache:**")
        instructions.append("   ```bash")
        instructions.append("   sudo sync")
        instructions.append("   sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'")
        instructions.append("   ```")
    elif fault_type == 'memory_exhaustion':
        instructions.append("## Steps to Fix Memory Exhaustion:")
        instructions.append("")
        instructions.append("1. **Check memory usage:**")
        instructions.append("   ```bash")
        instructions.append("   free -h")
        instructions.append("   ```")
        instructions.append("")
        instructions.append("2. **Kill memory-intensive processes:**")
        instructions.append("   ```bash")
        instructions.append("   ps aux --sort=-%mem | head -10")
        instructions.append("   kill -9 <PID>")
        instructions.append("   ```")
        instructions.append("")
        instructions.append("3. **Clear caches and restart services:**")
        instructions.append("   ```bash")
        instructions.append("   sudo sync")
        instructions.append("   sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'")
        instructions.append("   ```")
    elif fault_type == 'disk_full':
        instructions.append("## Steps to Fix Disk Full:")
        instructions.append("")
        instructions.append("1. **Check disk usage:**")
        instructions.append("   ```bash")
        instructions.append("   df -h")
        instructions.append("   ```")
        instructions.append("")
        instructions.append("2. **Clean up Docker resources:**")
        instructions.append("   ```bash")
        instructions.append("   docker system prune -a --volumes")
        instructions.append("   ```")
        instructions.append("")
        instructions.append("3. **Remove old logs:**")
        instructions.append("   ```bash")
        instructions.append("   sudo find /var/log -type f -name '*.log.*' -mtime +7 -delete")
        instructions.append("   ```")
        instructions.append("")
        instructions.append("4. **Clean apt cache:**")
        instructions.append("   ```bash")
        instructions.append("   sudo apt-get clean")
        instructions.append("   ```")
    elif fault_type == 'network_issue':
        instructions.append("## Steps to Fix Network Issue:")
        instructions.append("")
        instructions.append(f"1. **Check if container is running:**")
        instructions.append(f"   ```bash")
        instructions.append(f"   docker ps | grep {container_name}")
        instructions.append(f"   ```")
        instructions.append("")
        instructions.append("2. **Check port accessibility:**")
        port = fault.get('port', 0)
        if port > 0:
            instructions.append(f"   ```bash")
            instructions.append(f"   curl http://localhost:{port}/health")
            instructions.append(f"   ```")
        instructions.append("")
        instructions.append("3. **Restart network services:**")
        instructions.append("   ```bash")
        instructions.append("   sudo systemctl restart systemd-resolved")
        instructions.append("   ```")
        instructions.append("")
        instructions.append(f"4. **Restart the container:**")
        instructions.append(f"   ```bash")
        instructions.append(f"   docker restart {container_name}")
        instructions.append(f"   ```")
    
    if analysis and analysis.get('recommended_actions'):
        instructions.append("")
        instructions.append("## AI-Recommended Actions:")
        for i, action in enumerate(analysis.get('recommended_actions', []), 1):
            instructions.append(f"{i}. {action}")
    
    return "\n".join(instructions)

