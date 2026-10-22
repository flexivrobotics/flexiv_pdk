"""``license`` commands: see what this computer is licensed for, and license more.

``identifier`` / ``install`` / ``status``. Unlike every other command module,
none of these need an active workcell. See README_CLI.md for the workflow.
"""
import json
import pathlib

import click

from flexiv.pdk.license.license_service_pb2 import (
    GetDeviceIdentifierRequest,
    ListRequest,
)

from .._common import check, open_client, rpc


def _state_name(state):
    """LICENSE_STATE_NO_LICENSE -> "no license"."""
    from flexiv.pdk.license.license_service_pb2 import LicenseState

    name = LicenseState.Name(state)
    return name.replace("LICENSE_STATE_", "").replace("_", " ").lower()


def _is_licensed(service):
    from flexiv.pdk.license.license_service_pb2 import LicenseState

    return service.state == LicenseState.LICENSE_STATE_LICENSED


def _date_text(message, field):
    """A date, or "never" when the timestamp is unset - which means no expiry."""
    if not message.HasField(field):
        return "never"
    return getattr(message, field).ToDatetime().strftime("%Y-%m-%d")


def _expiry_text(service):
    """A date, "never" for a perpetual license, or "-" where there is none to expire."""
    if not _is_licensed(service):
        return "-"
    return _date_text(service, "expires")


def _detail_text(service):
    """The reason, when it says more than the LICENSE column already did.

    A plain unlicensed service needs no explanation - "no" covers it. Every other
    state does: expired, issued for another computer, unreadable security chip.
    That is what this column is for.
    """
    from flexiv.pdk.license.license_service_pb2 import LicenseState

    if service.state == LicenseState.LICENSE_STATE_NO_LICENSE:
        return ""
    return service.detail


def _print_services(services, as_json):
    """Render a repeated ServiceLicense the same way for every command returning one."""
    if as_json:
        click.echo(json.dumps([
            {
                "name": service.name,
                "display_name": service.display_name,
                "licensed": _is_licensed(service),
                "state": _state_name(service.state),
                "grpc_service": service.grpc_service,
                "detail": service.detail,
                "expires": _date_text(service, "expires"),
                "license_id": service.license_id,
            }
            for service in services
        ], indent=2))
        return

    if not services:
        click.echo("No licensable services reported by the server.")
        return

    width = max(len("SERVICE"), max(len(service.display_name) for service in services))
    click.echo(f"{'SERVICE':<{width}}  {'LICENSE':<9}{'EXPIRES':<12}DETAIL")
    for service in services:
        licensed = "yes" if _is_licensed(service) else "no"
        click.echo(
            f"{service.display_name:<{width}}  {licensed:<9}"
            f"{_expiry_text(service):<12}{_detail_text(service)}".rstrip()
        )


@click.group("license")
def license_group():
    """Show and install service licenses (no workcell needed)."""


@license_group.command("status")
@click.option("--json", "as_json", is_flag=True, help="Print machine-readable JSON.")
@click.pass_context
@rpc
def status(ctx, as_json):
    """Show which services this computer is licensed for."""
    client = open_client(ctx)
    response = check(
        client.license.stub.List(ListRequest()), "list licensed services")

    if as_json:
        _print_services(response.services, True)
        return

    click.echo(f"Security chip: {response.tpm_detail}")
    click.echo(f"Licenses in:   {response.license_directory}")
    click.echo("")
    _print_services(response.services, False)

    if response.licenses:
        click.echo("")
        for installed in response.licenses:
            hardware = "" if installed.hardware_verified else "  (chip not certified)"
            expires = _date_text(installed, "expires")
            click.echo(
                f"License {installed.license_id} for {installed.customer}, "
                f"expires {expires}{hardware}")

    # Problems with the folder rather than with one service: a file that will not
    # parse cannot say which services it covers, so it has nowhere else to appear.
    if response.warnings:
        click.echo("")
        click.echo("Problems:")
        for warning in response.warnings:
            click.echo(f"  {warning}")


@license_group.command("identifier")
@click.option("--output", "-o", "output", default="license_identifier.txt",
              type=click.Path(dir_okay=False, writable=True),
              show_default=True, help="Write the identifier to this file.")
@click.pass_context
@rpc
def identifier(ctx, output):
    """Write this computer's identifier to a file, to email to Flexiv."""
    client = open_client(ctx)
    response = check(
        client.license.stub.GetDeviceIdentifier(GetDeviceIdentifierRequest()),
        "get device identifier")

    path = pathlib.Path(output)
    try:
        path.write_text(response.identifier)
    except OSError as error:
        raise click.ClickException(f"Cannot write {path}: {error}")

    click.echo(f"Wrote {len(response.identifier)} bytes to {path.resolve()}")
    click.echo(
        "Attach that file to an email to Flexiv.")

    if not response.hardware_verifiable:
        click.echo("", err=True)
        click.echo(
            "Note: this computer's security chip has no manufacturer "
            "certificate. Mention this in the email.", err=True)


@license_group.command("install")
# -f is checked in the body rather than by required=True, so that someone
# following the old paste instructions is told what to do with the string in
# their hand instead of "Missing option '-f'".
@click.option("--file", "-f", "license_file", default=None,
              type=click.Path(exists=True, dir_okay=False, readable=True),
              help="The .lic file Flexiv sent back.  [required]")
@click.option("--file-name", default="",
              help="Save on the server as this name instead of the file's own.")
@click.argument("pasted", required=False)
@click.pass_context
@rpc
def install(ctx, license_file, file_name, pasted):
    """Install the .lic file Flexiv sent back. Takes effect immediately."""
    # A license used to be pasted as an argument. Say where it went, because
    # neither click's missing-option error nor its extra-argument error does.
    if pasted and not license_file:
        raise click.ClickException(
            "Save what Flexiv sent as a .lic file and pass it with -f <file.lic>.")
    if not license_file:
        raise click.ClickException(
            "Give the license file Flexiv sent with -f <file.lic>.")

    path = pathlib.Path(license_file)
    client = open_client(ctx)
    try:
        response = check(client.license.install_file(path, file_name),
                         "install license")
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error))

    click.echo(f"Installed {response.file_path}")
    if response.newly_licensed:
        from flexiv.pdk.license.license_service_pb2 import LicensedService

        names = ", ".join(
            LicensedService.Name(code).replace("LICENSED_SERVICE_", "").lower()
            for code in response.newly_licensed)
        click.echo(f"Newly licensed: {names}")
    else:
        click.echo("This license enabled nothing new.")
    click.echo("")
    _print_services(response.services, False)
