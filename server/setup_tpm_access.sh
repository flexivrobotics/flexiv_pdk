#!/bin/bash
# Lets THIS USER read the TPM directly, for running TPM diagnostics on the host.
#
# Nebula itself does not need this. The server runs inside the container, which
# reaches the chip through the device that docker_run.sh passes in, and that works
# whether or not the person who started it belongs to the 'tss' group.
#
# What this is for: running tpm_probe.sh, tpm2_getcap and the other tpm2-tools on
# the host, all of which open /dev/tpmrm0 as you rather than as the container.
#
#     bash setup_tpm_access.sh
#
# Then log out and back in - group membership only applies to new logins.
#
# If licensed services are switched off, this script is almost certainly not the
# fix: check that /dev/tpmrm0 exists on this computer, then re-run docker_run.sh
# so the container is given the device.

set -uo pipefail

echo "Flexiv Nebula - host TPM access, for diagnostics"
echo "================================================"
echo ""
echo "Nebula does not need this: the server reads the chip from inside the"
echo "container. This is for running tpm_probe.sh and tpm2-tools on the host."
echo ""

# ---------------------------------------------------------------------------
# Is there a TPM at all?
# ---------------------------------------------------------------------------
if [[ ! -e /dev/tpmrm0 && ! -e /dev/tpm0 ]]; then
  echo "No TPM 2.0 chip found on this computer (/dev/tpmrm0 is missing)."
  echo ""
  echo "The TPM may be switched off in the BIOS/UEFI setup - look for 'TPM',"
  echo "'Security Device', 'Intel PTT' or 'AMD fTPM' and enable it, then run"
  echo "this script again."
  echo ""
  echo "Nebula still runs without a TPM; licensed services stay switched off."
  exit 1
fi

if [[ ! -e /dev/tpmrm0 ]]; then
  echo "This computer has a TPM, but the kernel's TPM resource manager"
  echo "(/dev/tpmrm0) is not available. Nebula needs that interface."
  echo "A kernel newer than 4.12 provides it; check that the 'tpm_crb' or"
  echo "'tpm_tis' module is loaded."
  exit 1
fi

tpm_version="$(cat /sys/class/tpm/tpm0/tpm_version_major 2>/dev/null || echo unknown)"
if [[ "$tpm_version" != "2" ]]; then
  echo "Found a TPM reporting version '$tpm_version'. Nebula requires TPM 2.0."
  exit 1
fi
echo "Found a TPM 2.0 chip."

# ---------------------------------------------------------------------------
# Already done?
# ---------------------------------------------------------------------------
if ! getent group tss >/dev/null 2>&1; then
  echo ""
  echo "This system has no 'tss' group, which normally owns /dev/tpmrm0."
  echo "Install the TPM support package first:"
  echo "    sudo apt-get install tpm2-tools"
  echo "then run this script again."
  exit 1
fi

target_user="${SUDO_USER:-$USER}"

if id -nG "$target_user" 2>/dev/null | tr ' ' '\n' | grep -qx tss; then
  echo "User '$target_user' is already in the 'tss' group. Nothing to do."
  if [[ -r /dev/tpmrm0 && -w /dev/tpmrm0 ]]; then
    echo "TPM access is working in this shell."
  else
    echo ""
    echo "The group is set, but this shell does not have it yet."
    echo "Log out and back in, then start Nebula."
  fi
  exit 0
fi

# ---------------------------------------------------------------------------
# Grant it
# ---------------------------------------------------------------------------
echo ""
echo "About to run, as administrator:"
echo ""
echo "    sudo usermod -aG tss $target_user"
echo ""
echo "This adds '$target_user' to the 'tss' group so Nebula can read the TPM."
echo "It changes nothing else, and grants no other privileges."
echo ""
read -r -p "Continue? [y/N] " reply
if [[ ! "$reply" =~ ^[Yy]$ ]]; then
  echo "Cancelled. Nebula will run with licensed features switched off."
  exit 1
fi

if ! sudo usermod -aG tss "$target_user"; then
  echo ""
  echo "Could not add '$target_user' to the 'tss' group. Ask your system"
  echo "administrator to run: usermod -aG tss $target_user"
  exit 1
fi

echo ""
echo "Done. '$target_user' is now in the 'tss' group."
echo ""
echo "Log out and back in for it to take effect, then you can run:"
echo "    bash tool/license/tpm_probe.sh"
