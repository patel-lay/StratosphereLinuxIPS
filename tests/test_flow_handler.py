from tests.module_factory import ModuleFactory
import pytest

from unittest.mock import Mock, ANY, call
from slips_files.core.helpers.flow_handler import FlowHandler
from slips_files.core.flows.zeek import DHCP


def test_is_supported_flow_not_ts(flow, mock_db):
    flow.starttime = None
    flow_handler = ModuleFactory().create_flow_handler_obj(flow, mock_db)
    assert not flow_handler.is_supported_flow()


@pytest.mark.parametrize(
    "flow_type, expected_val",
    [
        ("dhcp", True),
        ("oscp", False),
        ("notice", True),
    ],
)
def test_is_supported_flow_without_ts(
    flow_type: str, expected_val: bool, flow, mock_db
):
    # just change the flow_type
    flow.type_ = flow_type
    flow_handler = ModuleFactory().create_flow_handler_obj(flow, mock_db)
    assert flow_handler.is_supported_flow() == expected_val


def test_handle_dns():
    mock_db = Mock()
    flow = Mock()
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.twid = "timewindow_id"
    flow_handler.profileid = "profile_id"
    flow_handler.handle_dns()

    mock_db.add_out_dns.assert_called_with(
        flow_handler.profileid,
        flow_handler.twid,
    )
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_ftp
def test_handle_ftp():
    mock_db = Mock()
    flow = Mock()
    flow.used_port = 21  # Assuming FTP typically uses port 21
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow_handler.handle_ftp()

    mock_db.set_ftp_port.assert_called_with(21)
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


def test_handle_http():
    mock_db = Mock()
    flow = Mock()
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow_handler.handle_http()

    mock_db.add_out_http.assert_called_with(
        flow_handler.profileid, flow_handler.twid, flow
    )
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_ssl
def test_handle_ssl(flow, mock_db):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow_handler.handle_ssl()

    mock_db.add_out_ssl.assert_called_with(
        flow_handler.profileid, flow_handler.twid, flow
    )
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_ssh
def test_handle_ssh(flow, mock_db):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow_handler.handle_ssh()

    mock_db.add_out_ssh.assert_called_with(
        flow_handler.profileid, flow_handler.twid, flow
    )
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_weird
def test_handle_weird(flow, mock_db):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow_handler.handle_weird()

    mock_db.publish.assert_called_with("new_weird", ANY)
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


def test_handle_tunnel(flow, mock_db):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow_handler.handle_tunnel()

    mock_db.publish.assert_called_with("new_tunnel", ANY)
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


def test_handle_conn(flow, mock_db, mocker):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow.daddr = "192.168.1.1"
    flow.dport = 80
    flow.proto = "tcp"

    mock_symbol = mocker.Mock()
    mock_symbol.compute.return_value = ("A", "B", "C")
    flow_handler.symbol = mock_symbol

    flow_handler.handle_conn()

    mock_db.add_tuple.assert_called_with(
        flow_handler.profileid,
        flow_handler.twid,
        "192.168.1.1-80-tcp",
        ("A", "B", "C"),
        "Client",
        flow,
    )
    mock_db.add_ips.assert_called_with(
        flow_handler.profileid, flow_handler.twid, flow, "Client"
    )
    mock_db.add_port.assert_has_calls(
        [
            call(
                flow_handler.profileid,
                flow_handler.twid,
                flow,
                "Client",
                "Dst",
            ),
            call(
                flow_handler.profileid,
                flow_handler.twid,
                flow,
                "Client",
                "Src",
            ),
        ]
    )
    mock_db.add_flow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )
    mock_db.add_mac_addr_to_profile.assert_called_with(
        flow_handler.profileid, flow.smac
    )
    if not flow_handler.running_non_stop:
        flow_handler.publisher.new_MAC.assert_has_calls(
            [call(flow.smac, flow.saddr), call(flow.dmac, flow.daddr)]
        )


def test_handle_files(flow, mock_db, mocker):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"

    flow_handler.handle_files()

    mock_db.publish.assert_called_with("new_downloaded_file", ANY)
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_arp
def test_handle_arp(flow, mock_db, mocker):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow.dmac = "aa:bb:cc:dd:ee:ff"
    flow.smac = "ff:ee:dd:cc:bb:aa"
    flow.daddr = "192.168.1.1"
    flow.saddr = "192.168.1.2"

    mock_publisher = mocker.Mock()
    flow_handler.publisher = mock_publisher

    flow_handler.handle_arp()

    mock_db.publish.assert_called_with("new_arp", ANY)
    mock_db.add_mac_addr_to_profile.assert_called_with(
        flow_handler.profileid, flow.smac
    )
    mock_publisher.new_MAC.assert_has_calls(
        [call(flow.dmac, flow.daddr), call(flow.smac, flow.saddr)]
    )
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_smtp
def test_handle_smtp(flow, mock_db):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"

    flow_handler.handle_smtp()

    mock_db.publish.assert_called_with("new_smtp", ANY)
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_software
def test_handle_software(flow, mock_db, mocker):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"

    mock_publisher = mocker.Mock()
    flow_handler.publisher = mock_publisher

    flow_handler.handle_software()

    mock_db.add_software_to_profile.assert_called_with(
        flow_handler.profileid, flow
    )
    mock_publisher.new_software.assert_called_with(
        flow_handler.profileid, flow
    )
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_notice
def test_handle_notice(flow, mock_db):
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"
    flow.note = "Gateway_addr_identified: 192.168.1.1"
    flow.msg = "Gateway_addr_identified: 192.168.1.1"

    flow_handler.handle_notice()

    mock_db.add_out_notice.assert_called_with(
        flow_handler.profileid, flow_handler.twid, flow
    )
    mock_db.set_default_gateway.assert_called_with("IP", "192.168.1.1")
    mock_db.add_altflow.assert_called_with(
        flow, flow_handler.profileid, flow_handler.twid, "benign"
    )


# testing handle_dhcp
def test_handle_dhcp(mock_db, mocker):
    flow = DHCP(
        starttime=1234567890,
        uids=["uid1", "uid2", "uid3"],
        smac="aa:bb:cc:dd:ee:ff",
        saddr="192.168.1.1",
        server_addr="192.168.1.1",
        daddr="192.168.1.2",
        client_addr="192.168.1.3",
        host_name="test-host",
        requested_addr="192.168.1.4",
    )
    flow_handler = FlowHandler(mock_db, None, flow)
    flow_handler.profileid = "profile_id"
    flow_handler.twid = "timewindow_id"

    mock_publisher = mocker.Mock()
    flow_handler.publisher = mock_publisher

    flow_handler.handle_dhcp()

    mock_publisher.new_MAC.assert_called_with(flow.smac, flow.saddr)
    mock_db.add_mac_addr_to_profile.assert_called_with(
        flow_handler.profileid, flow.smac
    )
    mock_db.store_dhcp_server.assert_called_with("192.168.1.1")
    mock_db.mark_profile_as_dhcp.assert_called_with(flow_handler.profileid)
    mock_publisher.new_dhcp.assert_called_with(flow_handler.profileid, flow)

    for uid in flow.uids:
        flow.uid = uid
        mock_db.add_altflow.assert_called_with(
            flow, flow_handler.profileid, flow_handler.twid, "benign"
        )
