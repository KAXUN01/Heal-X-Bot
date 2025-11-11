#!/usr/bin/env bash
# Heal-X-Bot Installer
# Installs required system dependencies to run the project on Debian/Ubuntu
# - Python 3.8+ (python3, python3-venv, python3-pip)
# - Docker Engine
# - Docker Compose (v2 plugin preferred; legacy docker-compose fallback)
# - Utilities: curl, ca-certificates, gnupg, lsof, net-tools, git
#
# Usage:
#   bash install.sh
#
# Notes:
# - You may be asked for your password for sudo operations.
# - After installation, you may need to log out/in for docker group changes to take effect.

set -euo pipefail
IFS=$'\n\t'

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

need_sudo() {
	if [ "$(id -u)" -ne 0 ]; then
		echo "sudo -n true >/dev/null 2>&1" | bash || return 0
	fi
	return 1
}

run_sudo() {
	if [ "$(id -u)" -eq 0 ]; then
		"$@"
	else
		sudo "$@"
	fi
}

require_cmd() {
	command -v "$1" >/dev/null 2>&1
}

detect_pkg_manager() {
	if require_cmd apt-get; then
		echo "apt"
	else
		echo ""
	fi
}

update_apt_if_needed() {
	echo -e "${YELLOW}🔄 Updating package index...${NC}"
	run_sudo apt-get update -y
}

install_pkgs_apt() {
	local pkgs=("$@")
	run_sudo apt-get install -y --no-install-recommends "${pkgs[@]}"
}

ensure_base_utils() {
	echo -e "${YELLOW}🔍 Ensuring base utilities...${NC}"
	install_pkgs_apt curl ca-certificates gnupg lsb-release apt-transport-https
	echo -e "${GREEN}✅ Base utilities ready${NC}"
}

ensure_python() {
	echo -e "${YELLOW}🐍 Ensuring Python 3.8+...${NC}"
	if require_cmd python3; then
		local ver
		ver="$(python3 --version 2>&1 | awk '{print $2}')"
		echo -e "${GREEN}   Found Python ${ver}${NC}"
	else
		update_apt_if_needed
		install_pkgs_apt python3
	fi
	# venv + pip
	if ! require_cmd pip3 || [ ! -d /usr/lib/python*/venv ] && [ ! -f /usr/bin/python3 -o ! -x /usr/bin/python3 ]; then
		update_apt_if_needed
		install_pkgs_apt python3-venv python3-pip
	else
		# Still ensure venv & pip packages exist
		update_apt_if_needed
		install_pkgs_apt python3-venv python3-pip || true
	fi
	echo -e "${GREEN}✅ Python ready${NC}"
}

install_docker_engine() {
	echo -e "${YELLOW}🐳 Installing Docker Engine (if needed)...${NC}"
	if require_cmd docker; then
		echo -e "${GREEN}   Docker already installed${NC}"
		return 0
	fi

	# Preferred: install from Docker's official repository
	local os_id=""
	local os_codename=""
	if [ -r /etc/os-release ]; then
		# shellcheck disable=SC1091
		. /etc/os-release
		os_id="${ID:-ubuntu}"
		os_codename="${VERSION_CODENAME:-$(lsb_release -cs 2>/dev/null || echo focal)}"
	fi

	update_apt_if_needed
	ensure_base_utils

	# Add Docker's official GPG key and repository
	run_sudo install -m 0755 -d /etc/apt/keyrings
	if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
		curl -fsSL https://download.docker.com/linux/${os_id}/gpg | run_sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
		run_sudo chmod a+r /etc/apt/keyrings/docker.gpg
	fi
	echo \
		"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${os_id} ${os_codename} stable" | \
		run_sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

	update_apt_if_needed
	install_pkgs_apt docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || {
		# Fallback to distro docker if official repo path fails
		echo -e "${YELLOW}⚠️  Falling back to distro Docker package (docker.io)${NC}"
		install_pkgs_apt docker.io
	}

	# Enable and start Docker service if present
	if require_cmd systemctl; then
		run_sudo systemctl enable docker || true
		run_sudo systemctl start docker || true
	fi

	echo -e "${GREEN}✅ Docker installed${NC}"
}

ensure_compose() {
	echo -e "${YELLOW}🔧 Ensuring Docker Compose...${NC}"
	if docker compose version >/dev/null 2>&1; then
		echo -e "${GREEN}   Compose v2 plugin available${NC}"
		return 0
	fi

	# Try installing the plugin via apt (already attempted in Docker install)
	if require_cmd apt-get; then
		update_apt_if_needed
		install_pkgs_apt docker-compose-plugin || true
		if docker compose version >/dev/null 2>&1; then
			echo -e "${GREEN}✅ Compose v2 plugin installed${NC}"
			return 0
		fi
	fi

	# Legacy docker-compose as a fallback
	if require_cmd docker-compose; then
		echo -e "${GREEN}   Legacy docker-compose available${NC}"
		return 0
	fi

	update_apt_if_needed
	install_pkgs_apt docker-compose || {
		echo -e "${YELLOW}⚠️  Could not install legacy docker-compose via apt${NC}"
	}

	if docker compose version >/dev/null 2>&1 || require_cmd docker-compose; then
		echo -e "${GREEN}✅ Docker Compose available${NC}"
	else
		echo -e "${RED}❌ Docker Compose installation failed${NC}"
		exit 1
	fi
}

ensure_dev_utils() {
	echo -e "${YELLOW}🧰 Ensuring developer utilities...${NC}"
	update_apt_if_needed
	install_pkgs_apt lsof net-tools git
	echo -e "${GREEN}✅ Developer utilities ready${NC}"
}

add_user_to_docker_group() {
	if getent group docker >/dev/null 2>&1; then
		if id -nG "$USER" | grep -qw docker; then
			echo -e "${GREEN}✅ User '$USER' already in docker group${NC}"
		else
			echo -e "${YELLOW}👤 Adding '$USER' to docker group...${NC}"
			run_sudo usermod -aG docker "$USER" || true
			echo -e "${YELLOW}ℹ️  You must log out and log back in (or run 'newgrp docker') to use Docker without sudo.${NC}"
		fi
	else
		echo -e "${YELLOW}⚠️  'docker' group not found; creating...${NC}"
		run_sudo groupadd docker || true
		run_sudo usermod -aG docker "$USER" || true
		echo -e "${YELLOW}ℹ️  Please re-login or run 'newgrp docker' to refresh your groups.${NC}"
	fi
}

verify_install() {
	echo -e "${YELLOW}🔎 Verifying installations...${NC}"
	echo -n "Python: "; python3 --version || true
	echo -n "Pip: "; pip3 --version || true
	echo -n "Docker: "; docker --version || true
	if docker compose version >/dev/null 2>&1; then
		echo -n "Docker Compose (v2): "; docker compose version || true
	else
		echo -n "Docker Compose (legacy): "; docker-compose --version || true
	fi
	echo -e "${GREEN}✅ Verification complete${NC}"
}

main() {
	echo -e "${YELLOW}🧪 Checking environment...${NC}"
	local pkg_mgr
	pkg_mgr="$(detect_pkg_manager)"
	if [ -z "$pkg_mgr" ]; then
		echo -e "${RED}❌ Unsupported system. This script supports Debian/Ubuntu with apt.${NC}"
		exit 1
	fi

	if need_sudo; then
		echo -e "${YELLOW}🔐 This script requires sudo privileges for package installation.${NC}"
	fi

	ensure_base_utils
	ensure_python
	install_docker_engine
	ensure_compose
	ensure_dev_utils
	add_user_to_docker_group
	verify_install

	echo ""
	echo -e "${GREEN}🎉 Done!${NC}"
	echo -e "${YELLOW}Next steps:${NC}"
	echo -e "1) Open a new shell or run: newgrp docker"
	echo -e "2) Test Docker access: docker info"
	echo -e "3) Start the project: bash ./start.sh"
}

main "$@"


